"""
Trustfall Farms - operating data simulator.

Turns the assumptions log (data/assumptions.csv), the startup capex list
(data/startup_capex.csv) and the market plan (data/market_plan.csv) into
three seasons of weekly farm records.

It runs twice:
  * scenario "plan"   - exactly what the assumptions say, no surprises
  * scenario "actual" - the same farm with week-to-week noise and a few
                        realistic shocks (late frost, wildfire smoke, feed spike)

Comparing the two gives budget vs. actual. A fixed random seed means anyone
who reruns this gets the same "actual" numbers (reproducible).

Outputs (data/simulated/):
  sales.csv     one row per week x channel x product
  expenses.csv  one row per expense item and date
  labor.csv     owner hours per week x enterprise
  financing.csv loan proceeds and payments
  events.csv    the shocks applied to the actual scenario
"""
from pathlib import Path
import math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "simulated"
SEED = 2027
FIRST_YEAR = 2027          # season 1 = 2027, season 2 = 2028, season 3 = 2029
FARM_START_MONTH = 3       # operations begin in March of year 1


def load_assumptions():
    a = pd.read_csv(DATA / "assumptions.csv", comment="#")
    return dict(zip(a["key"], a["value"].astype(float)))


def by_year(A, prefix, y):
    """Look up a per-year assumption such as hens_y2."""
    return A[f"{prefix}_y{y}"]


def lay_rate(A, month):
    """Seasonal laying curve: peaks in June, lowest in December."""
    swing = (math.cos((month - 6) / 12 * 2 * math.pi) + 1) / 2   # 1 in June, 0 in Dec
    return A["lay_rate_winter"] + swing * (A["lay_rate_peak"] - A["lay_rate_winter"])


def season_weights(weeks):
    """Bell-shaped harvest curve over the market season, peaking in mid-August."""
    w = np.array([math.exp(-((d - 33) / 6.0) ** 2) for d in weeks])
    return w / w.sum()


def simulate(scenario, A, capex, markets):
    rng = np.random.default_rng(SEED)
    noisy = scenario == "actual"
    sales, expenses, labor, events = [], [], [], []

    def noise(sigma=0.12):
        return float(rng.lognormal(0, sigma)) if noisy else 1.0

    share = markets["demand_index"] / markets["demand_index"].sum()

    for y in (1, 2, 3):
        year = FIRST_YEAR + y - 1
        weeks = pd.date_range(f"{year}-01-04", f"{year}-12-31", freq="W-MON")
        in_season = [w for w in weeks if A["season_start_month"] <= w.month <= A["season_end_month"]]
        season_iso = [w.isocalendar().week for w in in_season]
        harvest = dict(zip(in_season, season_weights(season_iso)))

        # ---- shocks (actual scenario only) ----
        produce_hit = 1.0
        smoke_weeks, feed_spike_from = set(), None
        if noisy and y == 1:
            produce_hit = 0.85
            events.append((f"{year}-06-15", "Late frost", "Frost after transplanting cut year 1 produce by ~15%"))
        if noisy and y == 2:
            smoke_weeks = {w for w in in_season if w.month == 8 and w.day > 7 and w.day <= 21}
            events.append((f"{year}-08-08", "Wildfire smoke", "Two Oregon market days cancelled for smoke"))
        if noisy and y == 3:
            feed_spike_from = pd.Timestamp(f"{year}-06-01")
            events.append((f"{year}-06-01", "Feed price spike", "Purchased feed up 12% from June"))

        hens, fryers = by_year(A, "hens", y), by_year(A, "fryers", y)
        bed_feet, rev_bf = by_year(A, "bed_feet", y), by_year(A, "rev_per_bed_ft", y)
        offset = by_year(A, "feed_garden_offset", y)
        produce_season_rev = bed_feet * rev_bf * produce_hit
        hives = A.get(f"hives_y{y}", 0)

        for w in weeks:
            if y == 1 and w.month < FARM_START_MONTH:
                continue
            m = w.month
            season = w in harvest
            feed_mult = 1.12 if (feed_spike_from is not None and w >= feed_spike_from) else 1.0
            laying = not (y == 1 and m < 4)          # hens arrive in April of year 1

            # ---------- EGGS ----------
            if laying:
                dozens = hens * lay_rate(A, m) * 7 / 12
                if season:
                    sold = dozens * 0.92 * noise()
                    for (_, mk), s in zip(markets.iterrows(), share):
                        lost = mk["state"] == "OR" and w in smoke_weeks
                        q = 0 if lost else min(sold * s, dozens * s)
                        sales.append((w, y, mk["market"], "Eggs", q, "dozen", q * A["egg_price"]))
                    sold_total = sum(r[4] for r in sales[-len(markets):])
                else:
                    sold_total = dozens * 0.80 * noise()
                    sales.append((w, y, "Farm direct", "Eggs", sold_total, "dozen", sold_total * A["egg_price"]))
                expenses.append((w, y, "Eggs", "Egg cartons", sold_total * A["egg_carton_cost"]))
                expenses.append((w, y, "Eggs", "Layer feed",
                                 hens * A["layer_feed_lb_per_hen_day"] * 7 * A["layer_feed_price"] * (1 - offset) * feed_mult))
                labor.append((w, y, "Eggs", A["hours_eggs_per_day"] * 7))

            # ---------- RABBITS ----------
            if 3 <= m <= 10:   # grow-out season
                expenses.append((w, y, "Rabbits", "Rabbit feed",
                                 fryers * A["rabbit_feed_per_fryer"] / 35 * (1 - offset) * feed_mult))
            expenses.append((w, y, "Rabbits", "Doe upkeep", A["does"] * A["doe_upkeep"] / 52 * (1 - offset)))
            labor.append((w, y, "Rabbits", A["hours_rabbits_per_day"] * 7))
            fresh = fryers * 0.70 / max(len(harvest), 1) if season else 0
            frozen = fryers * 0.30 / 12 if (not season and (y > 1 or m >= 11)) else 0
            if season:
                for (_, mk), s in zip(markets.iterrows(), share):
                    lost = mk["state"] == "OR" and w in smoke_weeks
                    q = 0 if lost else fresh * s * noise()
                    sales.append((w, y, mk["market"], "Rabbit", q * A["dressed_lb_per_fryer"], "lb",
                                  q * A["dressed_lb_per_fryer"] * A["rabbit_price"]))
                    expenses.append((w, y, "Rabbits", "Processing supplies", q * A["processing_supplies"]))
            elif frozen:
                q = frozen * noise()
                sales.append((w, y, "Farm direct", "Rabbit", q * A["dressed_lb_per_fryer"], "lb",
                              q * A["dressed_lb_per_fryer"] * A["rabbit_price"]))
                expenses.append((w, y, "Rabbits", "Processing supplies", q * A["processing_supplies"]))

            # ---------- PRODUCE, COTTAGE, HONEY, ORCHARD (market season) ----------
            if season:
                for (_, mk), s in zip(markets.iterrows(), share):
                    if mk["state"] == "OR" and w in smoke_weeks:
                        continue
                    # smaller markets sell through less of what you bring
                    sell_through = 0.75 + 0.25 * mk["demand_index"] if noisy else 1.0
                    prod = produce_season_rev * harvest[w] * s * sell_through * noise()
                    sales.append((w, y, mk["market"], "Produce", prod, "$", prod))
                    honey = 0.0
                    if hives and m >= 8:
                        honey_lb = hives * A["honey_lb_per_hive"] / 9 * s * noise()
                        honey = honey_lb * A["honey_price"]
                        sales.append((w, y, mk["market"], "Honey", honey_lb, "lb", honey))
                    if y == 3 and m >= 9:
                        fruit = A["orchard_rev_y3"] / 9 * s * noise()
                        sales.append((w, y, mk["market"], "Orchard fruit", fruit, "$", fruit))
                    market_day = sum(r[6] for r in sales if r[0] == w and r[2] == mk["market"])
                    cottage = market_day * A["cottage_share"] * noise()
                    sales.append((w, y, mk["market"], "Cottage foods", cottage, "$", cottage))
                    expenses.append((w, y, "Produce", "Produce packaging", prod * A["produce_packaging_pct"]))
                    key = "yreka" if mk["state"] == "CA" else "rv"
                    expenses.append((w, y, "Markets", "Booth fee", mk["booth_fee"]))
                    expenses.append((w, y, "Markets", "Mileage", mk["round_trip_mi"] * A["mileage_rate"]))
                    labor.append((w, y, "Markets", A["hours_per_market_day"]))
                labor.append((w, y, "Produce", A["hours_garden_per_week"]))
            else:
                labor.append((w, y, "Produce", A["hours_garden_offseason_per_week"]))

            # ---------- BEES AND ORCHARD CARE ----------
            if hives and 4 <= m <= 10:
                labor.append((w, y, "Honey", hives * A["hours_per_hive_per_month"] * 12 / 52))
            labor.append((w, y, "Orchard", A["orchard_hours_per_year"] / 52))

            # ---------- PRODUCE INPUTS (spring) ----------
            if 3 <= m <= 5:
                expenses.append((w, y, "Produce", "Seed and amendments", bed_feet * A["seed_amendment_cost"] / 13))

        # ---------- FIXED COSTS ----------
        first_month = FARM_START_MONTH if y == 1 else 1
        expenses.append((pd.Timestamp(f"{year}-{first_month:02d}-01"), y, "Fixed", "Insurance", A["insurance_annual"]))
        expenses.append((pd.Timestamp(f"{year}-{first_month:02d}-01"), y, "Fixed", "Licenses and permits", A["permits_annual"]))
        for m in range(first_month, 13):
            expenses.append((pd.Timestamp(f"{year}-{m:02d}-01"), y, "Fixed", "Utilities", A["utilities_monthly"]))

    # ---------- STARTUP CAPEX ----------
    for _, c in capex.iterrows():
        expenses.append((pd.Timestamp(f"{FIRST_YEAR + c['year'] - 1}-{int(c['month']):02d}-01"),
                         int(c["year"]), "Capex", c["item"], float(c["cost"])))

    # ---------- SHARED ASSETS: the farm carries only its business-use share ----------
    expenses.append((pd.Timestamp(f"{FIRST_YEAR}-03-01"), 1, "Capex", "Solar array (farm share)",
                     A["solar_cost"] * A["solar_farm_share"]))
    expenses.append((pd.Timestamp(f"{FIRST_YEAR}-03-01"), 1, "Capex", "Truck (farm share)",
                     A["truck_cost"] * A["truck_farm_share"]))

    # ---------- FINANCING: loan in, monthly payments out ----------
    financing = []
    if A["loan_amount"] <= 0:      # savings-funded: no loan rows
        return _frames(sales, expenses, labor, financing, events, scenario)
    P, r, n = A["loan_amount"], A["loan_rate"] / 12, int(A["loan_years"] * 12)
    pmt = P * r / (1 - (1 + r) ** -n)
    financing.append((pd.Timestamp(f"{FIRST_YEAR}-03-01"), 1, "Loan proceeds", P, 0.0, 0.0))
    balance = P
    for k in range(36):          # first three years of payments
        d = pd.Timestamp(f"{FIRST_YEAR}-04-01") + pd.DateOffset(months=k)
        interest = balance * r
        principal = pmt - interest
        balance -= principal
        financing.append((d, d.year - FIRST_YEAR + 1, "Loan payment", -pmt, interest, principal))

    return _frames(sales, expenses, labor, financing, events, scenario)


def _frames(sales, expenses, labor, financing, events, scenario):
    sales = pd.DataFrame(sales, columns=["week", "season", "channel", "product", "qty", "unit", "revenue"])
    expenses = pd.DataFrame(expenses, columns=["date", "season", "enterprise", "item", "amount"])
    labor = pd.DataFrame(labor, columns=["week", "season", "enterprise", "hours"])
    financing = pd.DataFrame(financing, columns=["date", "season", "type", "cash", "interest", "principal"])
    for df in (sales, expenses, labor, financing):
        df.insert(0, "scenario", scenario)
    events = pd.DataFrame(events, columns=["date", "event", "description"])
    return sales, expenses, labor, financing, events


def main():
    A = load_assumptions()
    capex = pd.read_csv(DATA / "startup_capex.csv")
    markets = pd.read_csv(DATA / "market_plan.csv")
    OUT.mkdir(parents=True, exist_ok=True)
    runs = [simulate(s, A, capex, markets) for s in ("plan", "actual")]
    names = ["sales", "expenses", "labor", "financing"]
    for i, name in enumerate(names):
        df = pd.concat([run[i] for run in runs], ignore_index=True)
        df = df.round({c: 2 for c in df.select_dtypes("number").columns})
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name:10s} {len(df):6,d} rows")
    runs[1][4].to_csv(OUT / "events.csv", index=False)
    print("events    ", len(runs[1][4]), "rows")


if __name__ == "__main__":
    main()

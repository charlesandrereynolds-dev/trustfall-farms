// Trustfall Farms - site content.
// The pipeline will regenerate the "deliverables" sections of this file
// from analysis outputs. Hand-edit text here until then.
window.TRUSTFALL = {
  farm: {
    name: "Trustfall Farms",
    tagline: "From business idea to business intelligence: a semi-fictional small permaculture farm in Northern California / Southern Oregon, run by a team of analytics workers.",
    disclaimer: "Trustfall Farms is fictional. Market anchors come from public sources; operating data is simulated and calibrated to them."
  },
  stages: [
    "Idea & market research",
    "Feasibility & startup budget",
    "Year 1: launch",
    "Year 2: adjust",
    "Year 3: steady state",
    "The decision"
  ],
  hub: {
    name: "Output hub", place: "Farmhouse",
    role: "Rolls every worker's output into one decision view.",
    short: ["Concept brief", "Go / no-go", "Year 1 review", "Year 2 review", "3-year BI", "Recommendation"],
    outputs: [
      "Business concept and market brief",
      "Feasibility go / no-go and funding plan",
      "Year 1 review: actuals vs. plan",
      "Year 2 review: what changed and why",
      "Three-season BI dashboard",
      "Weighted decision matrix and expansion recommendation"
    ]
  },
  // The four expansion options evaluated in "The decision" stage
  options: [
    "More pigs vs. a couple of cows",
    "Wedding and event flowers",
    "Online sales of value-added products",
    "Scale the winners: more acres and re-allocated grazing"
  ],
  // q, r = axial hex coordinates around the hub at (0, 0)
  workers: [
    {
      id: "intake", place: "Records barn", name: "Data intake", q: 0, r: -1, color: "#2f7d6b",
      role: "Pulls public data, cleans it, and checks it before anyone else uses it.",
      skills: ["Python", "SQL", "Data validation", "ETL"],
      tasks: [
        "Pull farmers-market directory and price data",
        "Load frost dates, climate normals and cost benchmarks",
        "Ingest year 1 sales and production logs",
        "Validate year 2 data; flag anomalies",
        "Three-season warehouse with quality checks",
        "Assemble the evidence base for each option"
      ]
    },
    {
      id: "forecast", place: "Crop fields", name: "Forecaster", q: 1, r: -1, color: "#3f6ea8",
      role: "Turns history and seasonality into forward-looking numbers.",
      skills: ["Time series", "Seasonality", "Scenario modeling"],
      tasks: [
        "Estimate seasonal demand by product",
        "Project year 1 output inside a ~110-day season",
        "Weekly harvest vs. sales forecast",
        "Re-forecast with year 1 actuals",
        "Trend and seasonality across three seasons",
        "Five-year output forecast for each option"
      ]
    },
    {
      id: "budget", place: "Farm office", name: "Budget", q: 1, r: 0, color: "#b07a1f",
      role: "Plans the money: what it costs to start, when it breaks even.",
      skills: ["FP&A", "Cash flow", "Budget vs. actual", "Unit economics"],
      tasks: [
        "Rough-order startup cost estimate",
        "Startup capex, 3-year cash flow and break-even",
        "Monthly budget vs. actual variance",
        "Feed-cost savings as the feed garden matures",
        "Unit economics by enterprise",
        "Capex, payback and NPV for each option"
      ]
    },
    {
      id: "risk", place: "Weather station", name: "Risk officer", q: 0, r: 1, color: "#b4483a",
      role: "Finds what could go wrong, sizes it, and sets early warnings.",
      skills: ["Risk register", "Monte Carlo", "KRIs", "Scenario analysis"],
      tasks: [
        "Initial risk register",
        "Frost, drought and wildfire exposure; cash runway",
        "Key risk indicators and thresholds",
        "Year 2 incident review and mitigations",
        "Risk heat map; how diversification cushioned bad years",
        "Downside scenarios and risk score for each option"
      ]
    },
    {
      id: "market", place: "Market stall", name: "Market scout", q: -1, r: 1, color: "#6b5aa6",
      role: "Sizes the opportunity and picks where and what to sell.",
      skills: ["Market sizing", "Geospatial", "Pricing"],
      tasks: [
        "Size demand; compare three markets on traffic, fees and price",
        "Map drive times; set launch prices",
        "Sell-through by market and week",
        "Drop weak products; test price changes",
        "Rank markets and products by margin per trip",
        "Demand and pricing research for each option"
      ]
    },
    {
      id: "compliance", place: "Permit desk", name: "Compliance", q: -1, r: 0, color: "#4d6b2f",
      role: "Keeps the farm legal across two states' rules.",
      skills: ["Regulatory analysis", "Controls", "Documentation"],
      tasks: [
        "California vs. Oregon direct-sales rules",
        "Zoning, water and septic permits; license costs",
        "Labeling and egg-handling checks",
        "Annual compliance calendar",
        "Compliance testing results across three seasons",
        "Regulatory hurdles and costs for each option"
      ]
    }
  ]
};

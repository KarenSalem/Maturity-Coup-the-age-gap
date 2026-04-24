# Licensed Drivers

- Source CSV: https://data.transportation.gov/api/views/jm62-yva2/rows.csv?accessType=DOWNLOAD
- Dataset page: https://data.transportation.gov/Roadways-and-Bridges/Licensed-Drivers-by-Sex-and-Age-Groups-1963-2024-D/jm62-yva2/about_data
- Fields used: year, sex, age group, licensed-driver counts
- DL-20 rate tables used: 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024
- Fields used there: age group, drivers as percent of age-group population, by sex and total
- Primary editorial anchor: 18-year-old licensure rate
- Bridge chart: `licensed-drivers-youth-work-overlay.svg` and `licensed-drivers-youth-work-overlay.csv` combine BLS July youth LFPR with the 16-18 share of all licensed drivers, indexed to 1963 = 100.
- Oil-shock context: EIA Monthly Energy Review Table 9.4, "Retail Motor Gasoline and On-Highway Diesel Fuel Prices" (`https://www.eia.gov/totalenergy/data/browser/?tbl=T09.04`), especially the 1978-1980 jump in annual leaded regular gasoline prices.
- Bridge context chart: `licensed-drivers-gasoline-teen-context.svg` pairs that gasoline shock with the summer-work / teen-licensing overlay and a computed 18-year-old licensure share.
- Story rationale note: `licensed-drivers/licensed-drivers-youth-work-overlay/why-this-matters.md`
- Affordability package: `minimum-wage-car-affordability.svg`, `minimum-wage-car-affordability.html`, and `minimum-wage-car-affordability.csv` estimate annual used-vehicle purchases, vehicle insurance, and gasoline / motor oil spending, then divide the total by the federal minimum wage to show the hours required to fund a driving basket.
- Method note: the affordability package backcasts annual spending anchors from BLS CPI-U used-car and motor-vehicle-insurance series, uses EIA gasoline prices spliced from leaded regular through 1990 and all-grades gasoline after that, and fills the single 1968 used-car CPI gap by linear interpolation between 1967 and 1969.

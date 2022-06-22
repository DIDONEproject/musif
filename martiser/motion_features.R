
# Read data
aria_sils <- readxl::read_excel("Did03M-Son_regina-1730-Sarro(1.05)(0006)_SecciónA_silencios.xlsx",
                                sheet = 2, na = c("NA", ""))
aria_no_sils <- readxl::read_excel("Did03M-Son_regina-1730-Sarro(1.05)(0006)_SecciónA.xlsx",
                                   sheet = 2, na = c("NA", ""))

# Exclude the last 9 rows because they contain summaries of the data
aria_sils <- aria_sils[1:(nrow(aria_sils) - 9), ]
aria_no_sils <- aria_no_sils[1:(nrow(aria_no_sils) - 9), ]

# Assumes aria is a data frame in the same form as aria_sils or aria_no_sils
motion_features <- function(aria, plots = FALSE) {

  # Expand the midis by their repetitions to have a time series
  step <- 0.125
  midis_raw <- rep(x = aria$Midind, times = aria$Duration / step)

  # Speed and acceleration
  spe_raw <- diff(midis_raw) / step
  acc_raw <- diff(spe_raw) / step

  # Absolute means of speed and acceleration
  spe_avg_abs <- mean(abs(spe_raw), na.rm = TRUE)
  acc_avg_abs <- mean(abs(acc_raw), na.rm = TRUE)

  # Rolling mean to smooth the midis by +-1 compasses -- not required for
  # statistics based on means but important for detecting increasing sequences
  # with a tolerance.
  compass <- 4
  midis_smo <- zoo::rollmean(midis_raw, k = 2 * compass + 1, align = "center")
  spe_smo <- diff(midis_smo) / step
  acc_smo <- diff(spe_smo) / step

  # Diagnostic plots
  if (plots) {
    plot(midis_raw, pch = 16, type = "o", cex = 0.5)
    lines(midis_smo, pch = 16, type = "o", cex = 0.5, col = 2)
    plot(spe_smo, pch = 16, type = "o", cex = 0.5)
    plot(acc_smo, pch = 16, type = "o", cex = 0.5)
  }

  # Prolonged ascent/descent chunks in smoothed midis of the aria (allows for
  # small violations in the form of decrements/increments that do not
  # decrease/increase the rolling mean).
  rle_asc <- rle(diff(midis_smo) > 0)
  rle_dsc <- rle(diff(midis_smo) < 0)
  asc <- rle_asc$lengths[which(rle_asc$values)]
  dsc <- rle_dsc$lengths[which(rle_dsc$values)]

  # Average length of ascent/descent chunks of the aria
  asc_avg <- mean(asc)
  dsc_avg <- mean(dsc)

  # Proportion of ascent/descent chunks over the total of the aria
  asc_prp <- sum(asc) / (length(midis_smo) - 1)
  dsc_prp <- sum(dsc) / (length(midis_smo) - 1)

  # Features
  return(list("spe_avg_abs" = spe_avg_abs, "acc_avg_abs" = acc_avg_abs,
              "asc_avg" = asc_avg, "dsc_avg" = dsc_avg,
              "asc_prp" = asc_prp, "dsc_prp" = dsc_prp))

}

# Features
motion_features(aria_sils, plots = TRUE)
# motion_features(aria_no_sils, plots = TRUE)




K9!
# SPDX-License-Identifier: PMPL-1.0-or-later
# Robot Vacuum Configuration Validator (K9/Nickel).
#
# This component provides formal schema validation for the robot vacuum 
//! simulator. It ensures that the virtual environment and the robot's 
//! physical properties are consistent and realistic.

# METADATA: Identifies this module as a 'Yard' component (Verification only).
leash = 'Yard

pedigree = {
  schema_version = "1.0.0",
  component_type = "config-validator",
  author = "Jonathan D.A. Jewell <jonathan.jewell@open.ac.uk>",
  description = "Validates robot vacuum simulation configurations",
  created = "2026-01-30",
  k9_spec_version = "1.0.0",
}

# CONFIGURATION SCHEMAS: Domain-specific record definitions.
schemas = {
  # ROBOT: Validates physical dimensions, navigation algorithms, and battery specs.
  robot_config = {
    name | String,
    dimensions = {
      diameter_cm | Number | std.number.between 10 50,
      height_cm   | Number | std.number.between 5 20,
    },
    navigation = {
      # ALGORITHM SELECTION: Must be one of the supported symbolic planners.
      algorithm | [| 'AStar, 'Spiral, 'Zigzag, 'WallFollow, 'Random |],
    },
    battery = {
      capacity_mah | Number | std.number.is_nat,
      voltage_v    | Number | std.number.between 3.0 24.0,
    }
  },

  # ENVIRONMENT: Validates the room layout and obstacle map.
  environment_config = {
    name | String,
    dimensions = {
      width_m  | Number | std.number.between 1 20,
      height_m | Number | std.number.between 1 20,
    },
    floor_type | [| 'Hardwood, 'Carpet, 'Tile, 'Mixed |],
  }
}

# VALIDATION CONTRACTS: Higher-order functions that verify cross-record constraints.
validation = {
  # REALISM: The robot's diameter must be significantly smaller than the room dimensions.
  robot_fits_environment = fun robot_config env_config =>
    let robot_diameter_m = robot_config.dimensions.diameter_cm / 100.0 in
    robot_diameter_m < env_config.dimensions.width_m &&
    robot_diameter_m < env_config.dimensions.height_m,

  # PERFORMANCE: The battery capacity must be sufficient for the requested simulation duration.
  battery_sufficient = fun robot_config sim_config =>
    let runtime_minutes = sim_config.duration_seconds / 60.0 in
    let max_runtime = robot_config.battery.capacity_mah / robot_config.battery.discharge_rate_ma * 60.0 in
    runtime_minutes <= max_runtime,
}

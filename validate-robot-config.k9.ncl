K9!
# SPDX-License-Identifier: PMPL-1.0-or-later
# Robot Vacuum Configuration Validator
#
# This K9 component validates robot vacuum simulation configurations,
# ensuring navigation algorithms, sensor parameters, and environment
# settings are within valid ranges.

leash = 'Yard  # Nickel evaluation only, no execution

pedigree = {
  schema_version = "1.0.0",
  component_type = "config-validator",
  author = "Jonathan D.A. Jewell <jonathan.jewell@open.ac.uk>",
  description = "Validates robot vacuum simulation configurations",
  created = "2026-01-30",
  k9_spec_version = "1.0.0",
}

# Configuration schemas
schemas = {
  # Robot configuration schema
  robot_config = {
    name | String,

    # Physical parameters
    dimensions = {
      diameter_cm | Number
        | std.number.greater 0
        | std.number.less_or_eq 50,  # Max 50cm diameter
      height_cm | Number
        | std.number.greater 0
        | std.number.less_or_eq 20,  # Max 20cm height
      weight_kg | Number
        | std.number.greater 0
        | std.number.less_or_eq 10,  # Max 10kg weight
    },

    # Navigation algorithm
    navigation = {
      algorithm | [| 'AStar, 'Spiral, 'Zigzag, 'WallFollow, 'Random |],
      max_speed_mps | Number
        | std.number.greater 0
        | std.number.less_or_eq 1.0,  # Max 1 m/s
      turning_radius_cm | Number
        | std.number.greater 0
        | std.number.less_or_eq 30,
    },

    # Battery configuration
    battery = {
      capacity_mah | Number
        | std.number.is_nat
        | std.number.greater 0,
      voltage_v | Number
        | std.number.is_float
        | std.number.between 3.0 24.0,  # 3V to 24V range
      charge_time_minutes | Number
        | std.number.is_nat
        | std.number.greater 0
        | std.number.less_or_eq 480,  # Max 8 hours
      discharge_rate_ma | Number
        | std.number.is_nat
        | std.number.greater 0,
    },

    # Sensor configuration
    sensors = {
      obstacle_detection = {
        enabled | Bool,
        range_cm | Number
          | std.number.greater 0
          | std.number.less_or_eq 100,
        fov_degrees | Number
          | std.number.between 0 360,
      },

      cliff_detection = {
        enabled | Bool,
        threshold_cm | Number
          | std.number.greater 0
          | std.number.less_or_eq 10,
      },

      bumper = {
        enabled | Bool,
        sensitivity | [| 'Low, 'Medium, 'High |],
      },
    },

    # Cleaning configuration
    cleaning = {
      brush_rpm | Number
        | std.number.is_nat
        | std.number.between 100 5000,
      suction_power_pa | Number
        | std.number.is_nat
        | std.number.between 500 4000,
      cleaning_modes | Array [| 'Auto, 'Spot, 'Edge, 'Spiral, 'Zigzag, 'WallFollow, 'Random |],
    },
  },

  # Environment configuration schema
  environment_config = {
    name | String,

    # Room dimensions
    dimensions = {
      width_m | Number
        | std.number.greater 0
        | std.number.less_or_eq 20,  # Max 20m width
      height_m | Number
        | std.number.greater 0
        | std.number.less_or_eq 20,  # Max 20m height
      wall_height_cm | Number
        | std.number.greater 0
        | std.number.less_or_eq 300,  # Max 3m walls
    },

    # Obstacles
    obstacles | Array {
      type | [| 'Box, 'Circle, 'Polygon |],
      position = {
        x_m | Number,
        y_m | Number,
      },
      size = {
        width_m | Number | std.number.greater 0,
        height_m | Number | std.number.greater 0,
      } | default = { width_m = 0.5, height_m = 0.5 },
    },

    # Charging dock
    charging_dock = {
      position = {
        x_m | Number,
        y_m | Number,
      },
      size_cm | Number
        | std.number.greater 0
        | std.number.less_or_eq 100,
    },

    # Floor type
    floor_type | [| 'Hardwood, 'Carpet, 'Tile, 'Mixed |],

    # Dirt distribution (for simulation)
    dirt_density | Number
      | std.number.between 0.0 1.0,  # 0 = clean, 1 = very dirty
  },

  # Simulation configuration schema
  simulation_config = {
    duration_seconds | Number
      | std.number.is_nat
      | std.number.greater 0,

    time_step_ms | Number
      | std.number.is_nat
      | std.number.between 10 1000,  # 10ms to 1s time steps

    visualization = {
      enabled | Bool,
      update_rate_hz | Number
        | std.number.is_nat
        | std.number.between 1 60,  # 1 to 60 FPS
      show_sensors | Bool | default = true,
      show_path | Bool | default = true,
    },

    slam = {
      enabled | Bool,
      particle_count | Number
        | std.number.is_nat
        | std.number.between 100 10000,
      map_resolution_cm | Number
        | std.number.is_nat
        | std.number.between 1 100,
    },

    logging = {
      enabled | Bool,
      log_level | [| 'Debug, 'Info, 'Warn, 'Error |],
      log_file | String | default = "simulation.log",
    },
  },
}

# Validation contracts
validation = {
  # Validate robot is not too large for environment
  robot_fits_environment = fun robot_config env_config =>
    let robot_diameter_m = robot_config.dimensions.diameter_cm / 100.0 in
    robot_diameter_m < env_config.dimensions.width_m &&
    robot_diameter_m < env_config.dimensions.height_m
    | doc "Robot must fit in the environment",

  # Validate battery capacity supports cleaning time
  battery_sufficient = fun robot_config sim_config =>
    let runtime_minutes = sim_config.duration_seconds / 60.0 in
    let max_runtime = robot_config.battery.capacity_mah / robot_config.battery.discharge_rate_ma * 60.0 in
    runtime_minutes <= max_runtime
    | doc "Battery must last for simulation duration",

  # Validate charging dock is within environment bounds
  dock_in_bounds = fun env_config =>
    let dock_x = env_config.charging_dock.position.x_m in
    let dock_y = env_config.charging_dock.position.y_m in
    dock_x >= 0 && dock_x <= env_config.dimensions.width_m &&
    dock_y >= 0 && dock_y <= env_config.dimensions.height_m
    | doc "Charging dock must be within environment bounds",

  # Validate at least one cleaning mode is enabled
  has_cleaning_modes = fun robot_config =>
    std.array.length robot_config.cleaning.cleaning_modes > 0
    | doc "At least one cleaning mode must be enabled",

  # Validate SLAM particle count is reasonable for environment size
  slam_particles_appropriate = fun env_config sim_config =>
    if !sim_config.slam.enabled then
      true
    else
      let area_m2 = env_config.dimensions.width_m * env_config.dimensions.height_m in
      let particles_per_m2 = sim_config.slam.particle_count / area_m2 in
      particles_per_m2 >= 10.0 && particles_per_m2 <= 1000.0
    | doc "SLAM particle density should be between 10 and 1000 particles per m²",
}

# Example valid configurations
examples = {
  typical_robot = {
    name = "CleanBot 3000",
    dimensions = {
      diameter_cm = 35.0,
      height_cm = 9.5,
      weight_kg = 3.2,
    },
    navigation = {
      algorithm = 'Spiral,
      max_speed_mps = 0.3,
      turning_radius_cm = 15.0,
    },
    battery = {
      capacity_mah = 5000,
      voltage_v = 14.4,
      charge_time_minutes = 240,
      discharge_rate_ma = 800,
    },
    sensors = {
      obstacle_detection = {
        enabled = true,
        range_cm = 50,
        fov_degrees = 180,
      },
      cliff_detection = {
        enabled = true,
        threshold_cm = 5,
      },
      bumper = {
        enabled = true,
        sensitivity = 'Medium,
      },
    },
    cleaning = {
      brush_rpm = 2000,
      suction_power_pa = 2000,
      cleaning_modes = ['Auto, 'Spot, 'Edge],
    },
  } | schemas.robot_config,

  typical_environment = {
    name = "Living Room",
    dimensions = {
      width_m = 6.0,
      height_m = 8.0,
      wall_height_cm = 250,
    },
    obstacles = [
      {
        type = 'Box,
        position = { x_m = 3.0, y_m = 4.0 },
        size = { width_m = 1.0, height_m = 0.8 },
      },
      {
        type = 'Circle,
        position = { x_m = 1.5, y_m = 2.0 },
        size = { width_m = 0.5, height_m = 0.5 },
      },
    ],
    charging_dock = {
      position = { x_m = 0.5, y_m = 0.5 },
      size_cm = 40,
    },
    floor_type = 'Hardwood,
    dirt_density = 0.3,
  } | schemas.environment_config,

  typical_simulation = {
    duration_seconds = 600,  # 10 minutes
    time_step_ms = 100,      # 10 Hz simulation
    visualization = {
      enabled = true,
      update_rate_hz = 30,
      show_sensors = true,
      show_path = true,
    },
    slam = {
      enabled = true,
      particle_count = 1000,
      map_resolution_cm = 5,
    },
    logging = {
      enabled = true,
      log_level = 'Info,
      log_file = "robot_vacuum_sim.log",
    },
  } | schemas.simulation_config,
}

# Usage example for Julia/Rust implementations
metadata = {
  usage_example = "
    # In Julia simulation code:
    using Nickel  # Hypothetical Nickel bindings for Julia
    validator = load_nickel(\"validate-robot-config.k9.ncl\")
    config = load_config(\"my_robot.json\")
    result = validator.validate(config)
    if !result.valid
        error(\"Invalid configuration: $(result.errors)\")
    end
  ",

  integration_note = "This K9 component provides configuration validation for both Julia and Rust implementations of the robot vacuum simulator. It ensures physics parameters are realistic and simulation settings are sensible.",
}

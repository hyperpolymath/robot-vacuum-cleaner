;; SPDX-License-Identifier: MIT
;; Testing Report for Robot Vacuum Cleaner Project
;; Generated: 2025-12-29

(define testing-report
  `((metadata
     (version "1.0.0")
     (schema-version "1.0")
     (created "2025-12-29T12:00:00Z")
     (project "robot-vacuum-cleaner")
     (tested-by "Claude Code Testing Agent"))

    (environment
     (platform "linux")
     (os "Fedora 43")
     (kernel "6.17.12-300.fc43.x86_64")
     (julia-version "1.12.2")
     (rust-version "stable"))

    (summary
     (overall-status passed)
     (implementations
      ((name "julia")
       (tests-passed 816)
       (tests-failed 0)
       (status passed))
      ((name "rust")
       (tests-passed 39)
       (tests-failed 0)
       (status passed))))

    (julia-implementation
     (location "src/julia/RobotVacuum/")
     (package-name "RobotVacuum")
     (test-location "tests/julia/")

     (issues-fixed
      ((id "JL-001")
       (severity high)
       (file "src/types.jl")
       (description "Missing normalize function - Base.normalize not defined")
       (fix "Changed to LinearAlgebra.normalize"))

      ((id "JL-002")
       (severity high)
       (file "src/environment.jl")
       (description "reset! incorrectly scoped to Base")
       (fix "Removed Base. prefix from reset! function"))

      ((id "JL-003")
       (severity high)
       (file "Project.toml")
       (description "Missing DataStructures dependency")
       (fix "Added DataStructures = \"864edb3b-99cc-5e75-8d2d-829cb0a9cfe8\""))

      ((id "JL-004")
       (severity medium)
       (file "src/RobotVacuum.jl")
       (description "Missing exports for enums and functions")
       (fix "Added exports for RobotState, CleaningMode enums and helper functions"))

      ((id "JL-005")
       (severity medium)
       (file "src/environment.jl, src/robot.jl")
       (description "Missing helper functions set_cell!, get_cell, update_sensors!")
       (fix "Implemented missing functions"))

      ((id "JL-006")
       (severity high)
       (file "src/pathplanning.jl")
       (description "A* algorithm crashes on PriorityQueue duplicate keys")
       (fix "Added haskey check before enqueueing"))

      ((id "JL-007")
       (severity critical)
       (file "src/simulator.jl")
       (description "Random module shadowed by CleaningMode.Random enum value")
       (fix "Used import Random as Rng alias")))

     (test-results
      (total 816)
      (passed 816)
      (failed 0)
      (time-seconds 49.1)
      (modules
       ((name "Types") (tests 22))
       ((name "Robot") (tests 30))
       ((name "Environment") (tests 30))
       ((name "Path Planning") (tests 542))
       ((name "SLAM") (tests 124))
       ((name "Simulator") (tests 68)))))

    (rust-implementation
     (location "src/rust/")
     (crate-name "robot-vacuum-cleaner")
     (binary-name "robot-vacuum")

     (issues-fixed
      ((id "RS-001")
       (severity medium)
       (file "benches/pathfinding.rs, benches/slam.rs")
       (description "Missing benchmark files declared in Cargo.toml")
       (fix "Created stub benchmark files"))

      ((id "RS-002")
       (severity high)
       (file "src/simulator.rs")
       (description "Incorrect enum variant syntax using dot instead of double colon")
       (fix "Changed RobotState.Cleaning to RobotState::Cleaning"))

      ((id "RS-003")
       (severity medium)
       (file "src/main.rs")
       (description "CLI short option conflict between --slam and --start_x")
       (fix "Changed short options: -S for slam, -x/-y for coordinates")))

     (test-results
      (total 39)
      (passed 39)
      (failed 0)
      (modules
       ((name "environment") (tests 7))
       ((name "pathfinding") (tests 3))
       ((name "robot") (tests 11))
       ((name "simulator") (tests 2))
       ((name "slam") (tests 3))
       ((name "types") (tests 13)))))

    (runtime-validation
     (julia
      (command "julia --project=src/julia/RobotVacuum tests/julia/runtests.jl")
      (status passed)
      (simulation-test
       (room-type "empty")
       (max-steps 100)
       (result success)))

     (rust
      (command "cargo run -- -m 100 -v")
      (status passed)
      (simulation-test
       (room-size "50x50")
       (max-steps 100)
       (result success))))

    (recommendations
     (high-priority
      ("Implement actual robot movement in simulation step function"
       "Add integration tests for complete simulation scenarios"))

     (medium-priority
      ("Fix Rust compiler warnings for unused imports"
       "Add documentation tests with examples"))

     (low-priority
      ("Implement benchmark tests in Rust"
       "Add property-based testing using proptest")))

    (conclusion
     (status "healthy")
     (julia-issues-fixed 7)
     (rust-issues-fixed 3)
     (ready-for-development #t))))

;; Helper functions for querying the report
(define (get-overall-status)
  (cadr (assoc 'overall-status (cadr (assoc 'summary testing-report)))))

(define (get-issues-by-severity severity)
  (let* ((julia-issues (cadr (assoc 'issues-fixed
                                     (cadr (assoc 'julia-implementation testing-report)))))
         (rust-issues (cadr (assoc 'issues-fixed
                                    (cadr (assoc 'rust-implementation testing-report))))))
    (filter (lambda (issue)
              (eq? (cadr (assoc 'severity issue)) severity))
            (append julia-issues rust-issues))))

(define (get-total-tests)
  (let ((julia-total (cadr (assoc 'total
                                   (cadr (assoc 'test-results
                                                 (cadr (assoc 'julia-implementation testing-report)))))))
        (rust-total (cadr (assoc 'total
                                  (cadr (assoc 'test-results
                                                (cadr (assoc 'rust-implementation testing-report))))))))
    (+ julia-total rust-total)))

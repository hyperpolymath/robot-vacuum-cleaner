;; SPDX-License-Identifier: AGPL-3.0-or-later
;; SPDX-FileCopyrightText: 2025 Jonathan D.A. Jewell
;; ECOSYSTEM.scm — robot-vacuum-cleaner

(ecosystem
  (version "1.0.0")
  (name "robot-vacuum-cleaner")
  (type "project")
  (purpose "A comprehensive, production-grade robot vacuum cleaner simulation system with dual Julia and Rust implementations, GraphQL API, SLAM algorithms, and enterprise CI/CD infrastructure.")

  (position-in-ecosystem
    "Part of hyperpolymath ecosystem. Follows RSR guidelines.")

  (related-projects
    (project (name "rhodium-standard-repositories")
             (url "https://github.com/hyperpolymath/rhodium-standard-repositories")
             (relationship "standard")))

  (what-this-is "A comprehensive, production-grade robot vacuum cleaner simulation system with dual Julia and Rust implementations, GraphQL API, SLAM algorithms, and enterprise CI/CD infrastructure.")
  (what-this-is-not "- NOT exempt from RSR compliance"))

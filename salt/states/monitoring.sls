# Salt State: Monitoring and Observability Setup
# Configures Prometheus, Grafana, and other monitoring tools

{% set project_root = pillar.get('project_root', '/opt/robot-vacuum-cleaner') %}
{% set monitoring_dir = project_root + '/monitoring' %}

# Create monitoring directories
monitoring_base:
  file.directory:
    - name: {{ monitoring_dir }}
    - user: {{ pillar.get('user', 'developer') }}
    - group: {{ pillar.get('group', 'developer') }}
    - mode: 755
    - makedirs: True

prometheus_config_dir:
  file.directory:
    - name: {{ monitoring_dir }}/prometheus
    - user: {{ pillar.get('user', 'developer') }}
    - group: {{ pillar.get('group', 'developer') }}
    - mode: 755
    - require:
      - file: monitoring_base

grafana_config_dir:
  file.directory:
    - name: {{ monitoring_dir }}/grafana
    - user: {{ pillar.get('user', 'developer') }}
    - group: {{ pillar.get('group', 'developer') }}
    - mode: 755
    - require:
      - file: monitoring_base

# Prometheus configuration
prometheus_config:
  file.managed:
    - name: {{ monitoring_dir }}/prometheus.yml
    - contents: |
        global:
          scrape_interval: 15s
          evaluation_interval: 15s
          external_labels:
            monitor: 'robot-vacuum-monitor'

        # Alertmanager configuration
        alerting:
          alertmanagers:
            - static_configs:
                - targets: ['localhost:9093']

        # Load rules once and periodically evaluate them
        rule_files:
          - "alerts/*.yml"

        # Scrape configurations
        scrape_configs:
          # Prometheus self-monitoring
          - job_name: 'prometheus'
            static_configs:
              - targets: ['localhost:9090']

          # Robot Vacuum API
          - job_name: 'robot-vacuum-api'
            metrics_path: '/metrics'
            static_configs:
              - targets: ['api:8000']
            relabel_configs:
              - source_labels: [__address__]
                target_label: instance
                replacement: 'robot-vacuum-api'

          # Redis exporter
          - job_name: 'redis'
            static_configs:
              - targets: ['redis-exporter:9121']

          # PostgreSQL exporter
          - job_name: 'postgres'
            static_configs:
              - targets: ['postgres-exporter:9187']

          # Node exporter (system metrics)
          - job_name: 'node'
            static_configs:
              - targets: ['node-exporter:9100']

          # cAdvisor (container metrics)
          - job_name: 'cadvisor'
            static_configs:
              - targets: ['cadvisor:8080']
    - mode: 644
    - user: {{ pillar.get('user', 'developer') }}
    - require:
      - file: prometheus_config_dir

# Prometheus alerts configuration
prometheus_alerts_dir:
  file.directory:
    - name: {{ monitoring_dir }}/prometheus/alerts
    - user: {{ pillar.get('user', 'developer') }}
    - mode: 755
    - require:
      - file: prometheus_config_dir

prometheus_alerts:
  file.managed:
    - name: {{ monitoring_dir }}/prometheus/alerts/robot-vacuum.yml
    - contents: |
        groups:
          - name: robot_vacuum_alerts
            interval: 30s
            rules:
              # API is down
              - alert: APIDown
                expr: up{job="robot-vacuum-api"} == 0
                for: 1m
                labels:
                  severity: critical
                annotations:
                  summary: "Robot Vacuum API is down"
                  description: "API has been down for more than 1 minute"

              # High error rate
              - alert: HighErrorRate
                expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
                for: 5m
                labels:
                  severity: warning
                annotations:
                  summary: "High error rate detected"
                  description: "Error rate is {{ $value }} errors/sec"

              # Battery low
              - alert: RobotBatteryLow
                expr: robot_battery_level < 20
                for: 2m
                labels:
                  severity: warning
                annotations:
                  summary: "Robot battery is low"
                  description: "Battery level is {{ $value }}%"

              # Robot stuck
              - alert: RobotStuck
                expr: robot_stuck_count > 5
                for: 1m
                labels:
                  severity: warning
                annotations:
                  summary: "Robot is stuck"
                  description: "Robot has been stuck {{ $value }} times"

              # High memory usage
              - alert: HighMemoryUsage
                expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
                for: 5m
                labels:
                  severity: warning
                annotations:
                  summary: "High memory usage"
                  description: "Memory usage is above 90%"

              # High CPU usage
              - alert: HighCPUUsage
                expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
                for: 5m
                labels:
                  severity: warning
                annotations:
                  summary: "High CPU usage"
                  description: "CPU usage is above 80%"

              # Disk space low
              - alert: DiskSpaceLow
                expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
                for: 5m
                labels:
                  severity: warning
                annotations:
                  summary: "Low disk space"
                  description: "Disk space is below 10%"
    - mode: 644
    - require:
      - file: prometheus_alerts_dir

# Grafana datasources configuration
grafana_datasources_dir:
  file.directory:
    - name: {{ monitoring_dir }}/grafana/datasources
    - user: {{ pillar.get('user', 'developer') }}
    - mode: 755
    - require:
      - file: grafana_config_dir

grafana_datasources:
  file.managed:
    - name: {{ monitoring_dir }}/grafana/datasources/prometheus.yml
    - contents: |
        apiVersion: 1

        datasources:
          - name: Prometheus
            type: prometheus
            access: proxy
            url: http://prometheus:9090
            isDefault: true
            editable: true
            jsonData:
              timeInterval: "15s"
    - mode: 644
    - require:
      - file: grafana_datasources_dir

# Grafana dashboards configuration
grafana_dashboards_dir:
  file.directory:
    - name: {{ monitoring_dir }}/grafana/dashboards
    - user: {{ pillar.get('user', 'developer') }}
    - mode: 755
    - require:
      - file: grafana_config_dir

grafana_dashboard_provider:
  file.managed:
    - name: {{ monitoring_dir }}/grafana/dashboards/dashboards.yml
    - contents: |
        apiVersion: 1

        providers:
          - name: 'Robot Vacuum Dashboards'
            orgId: 1
            folder: ''
            type: file
            disableDeletion: false
            updateIntervalSeconds: 10
            allowUiUpdates: true
            options:
              path: /etc/grafana/provisioning/dashboards
    - mode: 644
    - require:
      - file: grafana_dashboards_dir

# Create sample Grafana dashboard JSON
grafana_robot_dashboard:
  file.managed:
    - name: {{ monitoring_dir }}/grafana/dashboards/robot-vacuum.json
    - contents: |
        {
          "dashboard": {
            "title": "Robot Vacuum Cleaner Dashboard",
            "tags": ["robot", "vacuum", "iot"],
            "timezone": "browser",
            "panels": [
              {
                "title": "Robot Status",
                "type": "stat",
                "targets": [
                  {
                    "expr": "robot_status",
                    "legendFormat": "Status"
                  }
                ]
              },
              {
                "title": "Battery Level",
                "type": "gauge",
                "targets": [
                  {
                    "expr": "robot_battery_level",
                    "legendFormat": "Battery %"
                  }
                ]
              },
              {
                "title": "Cleaning Coverage",
                "type": "graph",
                "targets": [
                  {
                    "expr": "robot_cleaning_coverage",
                    "legendFormat": "Coverage %"
                  }
                ]
              },
              {
                "title": "Distance Traveled",
                "type": "graph",
                "targets": [
                  {
                    "expr": "rate(robot_distance_total[5m])",
                    "legendFormat": "Distance (m/s)"
                  }
                ]
              },
              {
                "title": "API Request Rate",
                "type": "graph",
                "targets": [
                  {
                    "expr": "rate(http_requests_total[5m])",
                    "legendFormat": "{{method}} {{path}}"
                  }
                ]
              },
              {
                "title": "Error Rate",
                "type": "graph",
                "targets": [
                  {
                    "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
                    "legendFormat": "5xx errors"
                  }
                ]
              }
            ],
            "schemaVersion": 36,
            "version": 1
          }
        }
    - mode: 644
    - require:
      - file: grafana_dashboards_dir

# Install monitoring tools
monitoring_packages:
  pkg.installed:
    - pkgs:
      - prometheus
      - grafana

# Create monitoring helper scripts
start_monitoring:
  file.managed:
    - name: {{ project_root }}/scripts/start-monitoring.sh
    - contents: |
        #!/bin/bash
        cd {{ project_root }}
        echo "Starting monitoring stack..."
        podman-compose -f docker/compose.yaml --profile monitoring up -d
        echo "Monitoring services started!"
        echo "Prometheus: http://localhost:9090"
        echo "Grafana: http://localhost:3000 (admin/admin)"
    - mode: 755
    - user: {{ pillar.get('user', 'developer') }}
    - require:
      - file: monitoring_base

stop_monitoring:
  file.managed:
    - name: {{ project_root }}/scripts/stop-monitoring.sh
    - contents: |
        #!/bin/bash
        cd {{ project_root }}
        echo "Stopping monitoring stack..."
        podman-compose -f docker/compose.yaml --profile monitoring down
        echo "Monitoring services stopped!"
    - mode: 755
    - user: {{ pillar.get('user', 'developer') }}
    - require:
      - file: monitoring_base

# Monitoring setup complete
monitoring_complete:
  test.succeed_without_changes:
    - name: monitoring_setup_ready
    - require:
      - file: prometheus_config
      - file: prometheus_alerts
      - file: grafana_datasources
      - file: grafana_robot_dashboard
      - file: start_monitoring

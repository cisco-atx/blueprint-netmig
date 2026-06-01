# NetMig

## Overview

NetMig is a script-driven network migration automation framework within the ATX (Automation Tooling) platform.

It provides a centralized platform for managing, executing, and monitoring migration automation scripts through a web-based interface. NetMig allows network engineers to package migration logic as reusable modules, execute them on demand, monitor execution progress in real time, and collect migration artifacts and reports.

Rather than building individual migration tools directly into ATX, NetMig provides a pluggable architecture where migration workflows can be deployed as independent scripts and executed through a common framework.

This approach enables rapid development, standardized execution, and reusable automation across multiple migration projects.

---

## Why NetMig?

Network migration projects often require custom automation for activities such as:

* Device onboarding
* Configuration generation
* Data collection
* Migration validation
* Cutover execution
* Post-migration reporting
* Inventory transformation
* Bulk network changes

Traditionally these tools are developed as standalone scripts, making them difficult to manage, distribute, and reuse.

NetMig solves this problem by providing:

* Centralized script management
* Standardized execution framework
* Dynamic script loading
* Real-time execution monitoring
* Automated report generation
* Reusable migration workflows
* Self-service execution through ATX

---

## NetMig in ATX

NetMig is implemented as a Flask Blueprint and integrates directly into the ATX platform.

### Blueprint Metadata

| Property    | Value                           |
| ----------- | ------------------------------- |
| Name        | NetMig                          |
| Version     | 1.0.0                           |
| URL Prefix  | `/netmig`                       |
| Description | Script Management and Execution |

---

## Core Capabilities

### Dynamic Script Framework

NetMig automatically discovers migration scripts from a designated script repository.

Each script is loaded dynamically at runtime without requiring changes to the ATX core application.

This allows migration teams to deploy new automation modules independently while leveraging the existing execution framework.

---

### Script Lifecycle Management

NetMig provides a complete lifecycle for migration scripts.

Capabilities include:

* Script discovery
* Script registration
* Script validation
* Script execution
* Script monitoring
* Script output management

All scripts become immediately available through the NetMig user interface once loaded successfully.

---

### Centralized Script Repository

NetMig maintains a dedicated script repository under:

```text
~/.netmigweb/scripts
```

Each migration tool is deployed as a self-contained package.

Typical script structure:

```text
Migration Script
├── __init__.py
├── README.md
├── Templates
├── Libraries
└── Supporting Files
```

This enables migration teams to maintain automation independently from the ATX platform itself.

---

### Script Validation Framework

Before a script is registered, NetMig validates its structure to ensure consistency across all automation modules.

Each script must provide:

```python
meta
required()
input()
run()
```

Validation ensures that all migration tools follow a common execution model and user experience.

---

## Script Metadata

Every NetMig script exposes metadata describing its functionality.

Example:

```python
meta = {
    "name": "Migration Tool",
    "version": "1.0.0",
    "description": "Automates migration workflow"
}
```

Metadata is used to:

* Display available tools
* Build navigation menus
* Generate execution pages
* Present script information to users

---

## Dynamic Route Registration

NetMig supports automatic API and UI route registration.

When a script is loaded:

1. Script routes are discovered.
2. Routes are validated.
3. Endpoints are registered dynamically.
4. APIs become immediately available.

This allows individual migration tools to extend the ATX web interface without modifying the NetMig core framework.

---

## Script Execution Engine

NetMig includes a built-in execution engine responsible for managing migration tasks.

Features include:

* Task creation
* Execution management
* Context handling
* Output streaming
* Progress tracking
* Error reporting

Each execution runs as an isolated task with its own execution context.

---

## Asynchronous Execution

Migration scripts execute in separate background threads.

Benefits include:

* Non-blocking execution
* Multiple concurrent tasks
* Long-running workflow support
* Improved user experience

Users can continue interacting with ATX while migration tasks execute in the background.

---

## Real-Time Progress Monitoring

NetMig provides live execution feedback using Server-Sent Events (SSE).

Scripts can publish:

### Standard Output

```text
Migration Started
Collecting Device Data
Generating Configurations
```

### Error Messages

```text
Connection Failed
Device Authentication Error
```

### Dynamic UI Updates

Scripts can update specific page elements while execution is in progress.

This enables interactive migration workflows and live reporting.

---

## Script Context Framework

Each execution receives a dedicated ScriptContext object.

The context provides:

### Logging

```python
context.log("Processing Device")
```

### Error Reporting

```python
context.error("Connection Failed")
```

### Progress Updates

```python
context.set_progress(50)
```

### Dynamic HTML Updates

```python
context.set_html("results", html_content)
```

### File Generation

```python
context.save_file(...)
```

This creates a consistent development model for all migration tools.

---

## Output Management

NetMig automatically manages output artifacts generated during script execution.

Supported outputs include:

* Reports
* CSV files
* Excel files
* Configuration files
* JSON exports
* Generated templates
* Migration evidence

Outputs are stored within the user report directory and made available for download through the web interface.

---

## Script Deployment Methods

### Manual Upload

Migration tools can be uploaded directly through the NetMig interface.

Benefits:

* Quick deployment
* No server access required
* Easy testing and validation

---

### Git Repository Integration

NetMig can deploy scripts directly from Git repositories.

Workflow:

```text
Git Repository
        ↓
Clone Repository
        ↓
Validate Script
        ↓
Register Script
        ↓
Available in NetMig
```

Benefits:

* Version-controlled deployments
* Centralized script maintenance
* Simplified updates
* Team collaboration

---

## Migration Workflow

### Step 1 – Deploy Migration Tool

Deploy a migration script by:

* Uploading files
* Cloning a Git repository

NetMig validates and registers the tool automatically.

---

### Step 2 – Configure Inputs

Open the migration tool.

Provide required inputs such as:

* Device inventory
* Credentials
* VLAN mappings
* Migration parameters
* Configuration templates

Input forms are generated dynamically by the script itself.

---

### Step 3 – Execute Migration Workflow

Launch the migration task.

NetMig creates:

```text
Task
├── Execution Context
├── User Inputs
├── Configuration
└── Output Directory
```

The task executes in the background.

---

### Step 4 – Monitor Execution

Track progress through:

* Live console output
* Progress indicators
* Status updates
* Dynamic report sections

---

### Step 5 – Review Results

Download generated outputs including:

* Migration reports
* Configuration files
* Validation results
* Inventory exports
* Execution logs

---

## Architecture

### High-Level Architecture

```text
ATX
└── NetMig Blueprint
    ├── Script Repository
    ├── Script Registry
    ├── Dynamic Route Loader
    ├── Execution Runner
    ├── Task Manager
    ├── Output Streaming Engine
    └── Report Storage
```

---

### Component Overview

#### Blueprint Layer

Responsible for:

* Initialization
* Script discovery
* Route registration
* Database setup

#### Runner Service

Responsible for:

* Task creation
* Script execution
* Thread management
* Output streaming

#### Script Context

Responsible for:

* Logging
* Progress tracking
* Output generation
* UI updates

#### Management Routes

Responsible for:

* Uploading scripts
* Cloning repositories
* Deleting scripts
* Reloading scripts

#### Execution Routes

Responsible for:

* Rendering script pages
* Running tasks
* Streaming outputs
* Downloading artifacts

---

## Typical Network Migration Use Cases

NetMig can be used to automate:

* Switch Replacement Projects
* Core Migration Activities
* WAN Transformation Programs
* Data Center Migrations
* VLAN Migration Projects
* Device Configuration Generation
* Inventory Collection
* Bulk Configuration Changes
* Network Validation Workflows
* Migration Reporting
* Cutover Automation
* Post-Migration Verification

---

## Benefits

### Reusable Automation

Build once and reuse across multiple migration projects.

### Faster Project Delivery

Reduce manual execution effort and deployment time.

### Standardized Execution

Provides a common framework for all migration tools.

### Improved Visibility

Real-time execution monitoring and reporting.

### Simplified Deployment

Deploy migration tools without modifying the ATX core platform.

### Scalable Architecture

Supports multiple independent migration workflows within a single framework.

---

## Future Enhancements

Potential future enhancements include:

* Task Scheduling
* Script Version Management
* Script Marketplace
* RBAC Integration
* Distributed Execution Workers
* Workflow Chaining
* Execution History Dashboard
* Script Dependency Management
* Approval Workflows
* Multi-User Collaboration
* Containerized Execution Environments

---

## Summary

NetMig provides a modular and extensible automation framework for network migration projects within ATX. By combining dynamic script deployment, standardized execution, real-time monitoring, and artifact management into a single platform, NetMig enables engineers to rapidly develop, deploy, and operate migration automation workflows while maintaining consistency across large-scale network transformation initiatives.

# Exastro IT Automation Overview

Exastro IT Automation (ITA) is an open-source framework for digitizing and centrally managing system configuration. It manages system configuration information such as device information, configuration values, and work history, and can export this data as Excel files. It also provides functions for managing and executing system construction and operational configuration for each device as workflows, and can integrate with various platform construction tools.

## Features

- **Multiple interfaces and RBAC**: Operations can be performed from three types of interfaces (Web, Spreadsheet, REST API). Regardless of which interface is used, "who did what and when" is recorded. RBAC (Role-based access control) allows roles such as developer, worker, and operator to be defined, and permissions (view only / update / execute) can be controlled per role.
- **Grouping and history management of parameters**: System parameter information can be grouped and managed with history.
- **Analyze IaC and extract variables**: When Infrastructure as Code (IaC) is uploaded, it is first analyzed for errors. If no errors are found, variable names are extracted from the IaC description and managed. Since variable names are selected from a list, human errors such as typos do not occur.
- **Modularize IaC to improve reusability**: IaC (Playbooks, etc.) can be modularized and reassembled at work time instead of being used only once, enabling continued reuse.
- **Chain multiple automation tools together**: Multiple automation tools can be chained together to define a single work flow, and the input data required for the automation tools to operate is automatically generated (e.g., for Ansible: collecting and chaining the required Playbooks, and creating host_vars per node from parameters).
- **Pioneer mode, the last resort to keep automation from stopping**: If automation cannot be achieved with any Ansible module, inserting a manual step would halve the benefit of automation. As a last resort to keep automation going, ITA provides Pioneer mode—an Ansible module unique to ITA that can interact with a device over either ssh or telnet.
- **Monitor execution status in real time**: ITA places importance on being able to grasp execution status in real time, comparable to manual work. Execution results (work evidence) can be downloaded whenever needed, so work records are properly managed.

## Functions

- **Management Console function**: Manages registration/update/deletion of users, controls permissions for operation menus, and imports/exports the various data managed by Exastro IT Automation.
- **Build Material Management function**: Manages the IaC used by automation software (OSS). It integrates with Git on the backend and provides check-out/check-in status management on the frontend.
- **Basic Console function**: Provides functions commonly required when working with ITA, such as registering and managing device information (device list) and creating, managing, and executing Conductors (job flows).
- **Parameter/Host Group function**: Provides centralized and historical management of system configuration (parameters per host or per host group). Managed parameters can be freely defined, and parameter values can be linked to IaC (Playbook, etc.) variables.
- **Driver group corresponding to each automation software**: Supports multiple automation software products, providing an interface to control each one's IaC (Playbook, etc.). The behavior of the automation software can be encapsulated in a Movement (unit of work), which can be chained together as a Conductor (job flow).
  - **Movement**: A unit of construction/configuration work performed on each device using a construction tool.
  - **Conductor**: A unit representing a series of work. It is executed in association with an operation name, combining parts called Nodes to build a job flow that performs a series of construction/configuration tasks against multiple devices.
  - **Operation**: A unit of work execution. Scheduled work and execution history can be managed.

# djangospice

**Application Runtime Framework for building Django apps**

`djangospice` is the application runtime for building modular Django applications.

It is designed to provide a consistent foundation for building large Django application ecosystems without repeatedly implementing the same infrastructure in every application.

djangospice sits below application modules and provides common capabilities such as:

* Application and module infrastructure
* Base Django models and domain abstractions
* Events and event listeners
* Command-line interfaces
* UI components and widgets
* HTTP and HTMX responses
* Notifications
* Broadcasting and realtime communication
* Async utilities
* Tables and data presentation
* File handling
* Import and export utilities
* Common services and utilities

The goal is simple:

> **Build the infrastructure once, then let Django applications focus on their domain.**

---

## Architecture

djangospice is intended to sit at the foundation of a modular Django ecosystem:

```text
┌─────────────────────────────────────────────┐
│              Django Applications            │
│                                             │
│  CRM · Billing · HR · Academic · Workflow   │
│  Notifications · Documents · Helpdesk · ... │
└───────────────────────┬─────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────┐
│                 djangospice                 │
│                                             │
│  Events        CLI          UI / Widgets    │
│  Notifications Broadcasting  HTTP / HTMX    │
│  Async         Tables       Files           │
│  Imports       Exports      Services        │
│  Base Models   Utilities   Common APIs      │
└───────────────────────┬─────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────┐
│             Django / Python                 │
│                                             │
│       Django · Django ORM · ASGI · ...      │
└─────────────────────────────────────────────┘
```

Application modules depend on djangospice, while djangospice remains independent of any particular business domain.

---

## Why djangospice?

Large Django projects often accumulate infrastructure that gets duplicated across applications.

For example, individual applications may independently implement:

* Base models
* Event dispatching
* Notification delivery
* UI components
* HTMX responses
* CLI commands
* File handling
* Import/export pipelines
* Realtime broadcasting
* Table rendering
* Common service abstractions

djangospice provides these capabilities as a shared runtime.

This gives applications a common architecture and allows modules to remain focused on their actual domain.

### Design goals

djangospice is designed around several principles:

* **Reusable** — common functionality should be implemented once.
* **Modular** — functionality should be composed through independent components.
* **Extensible** — applications should be able to replace or extend framework behavior.
* **Django-native** — use Django's existing ecosystem rather than reinventing it.
* **Convention-driven** — provide consistent patterns across applications.
* **Domain-independent** — the runtime should not contain business-specific logic.
* **Composable** — services and components should work independently or together.
* **Developer-friendly** — common application infrastructure should require minimal boilerplate.

---

## Installation

Install djangospice from PyPI:

```bash
pip install djangospice
```

For development:

```bash
git clone https://github.com/briansimpo/djangospice.git
cd djangospice

pip install -e .
```

---

## Basic Usage

Once installed, djangospice components can be imported by Django applications and modules.

For example, using the common model infrastructure:

```python
from djangospice.database.models import BaseModel


class Customer(BaseModel):
    name = models.CharField(max_length=255)
```

The exact capabilities available depend on the components being used by the application.

---

# Core Components

djangospice is organized around reusable infrastructure rather than business-domain applications.

## Database and Models

Common Django model abstractions provide a consistent foundation for application models.

```python
from djangospice.database.models import BaseModel
```

The database layer is intended to eliminate repetitive model infrastructure while preserving normal Django ORM behavior.

---

## Events

The event system provides a decoupled mechanism for applications to communicate.

Instead of tightly coupling one application component to another, a component can dispatch an event and allow listeners to react to it.

Conceptually:

```text
Application Action
       │
       ▼
     Event
       │
       ├── Listener
       ├── Listener
       └── Listener
```

This allows functionality such as notifications, auditing, integrations, and background processing to be attached without modifying the original application logic.

---

## Notifications

djangospice provides infrastructure for building application notification systems.

The architecture separates:

```text
Notification
     │
     ├── Storage
     │
     ├── Presentation
     │
     └── Delivery
          ├── Email
          ├── SMS
          ├── Push
          ├── Websocket
          └── Other channels
```

This separation allows applications to change how notifications are delivered without changing the notification itself.

---

## Broadcasting and Realtime Communication

The runtime provides abstractions for broadcasting application events and data to users or groups.

For example:

```python
Broadcast.everyone(...)
```

or:

```python
Broadcast.user(user, ...)
```

This infrastructure can be used by applications that need realtime updates through WebSockets or other supported transports.

---

## UI and Widgets

djangospice provides reusable UI infrastructure for Django applications.

The widget architecture allows application components to encapsulate:

* Rendering
* Permissions
* Lazy loading
* Refresh behavior
* Caching
* HTTP/HTMX responses
* Data presentation

Applications can therefore build reusable UI components instead of duplicating view and template logic.

---

## HTMX

HTMX is treated as an application transport rather than something every application needs to implement independently.

djangospice provides response and rendering abstractions that allow components to return normal HTTP responses or HTMX-aware responses.

This makes it possible to build interactive Django applications while keeping the application code independent of individual response details.

---

## Tables

For tabular data, djangospice builds on established Django tooling rather than attempting to replace it.

Where appropriate, applications can use **django-tables2** as the underlying table engine while djangospice provides higher-level integration with the runtime and UI architecture.

---

## CLI

djangospice provides reusable command-line infrastructure for Django applications and modules.

This is particularly useful for application ecosystems where modules need consistent commands for tasks such as:

```text
installation
configuration
initialization
data import
data export
maintenance
module management
```

The goal is to provide a common CLI experience instead of every module implementing its own command infrastructure.

---

## Async Support

The runtime provides common abstractions for asynchronous application functionality.

This allows modules to use async operations where appropriate while keeping common infrastructure in one place.

---

## Files

djangospice provides common abstractions for file-related functionality, allowing applications to work with files without repeatedly implementing storage and file-handling patterns.

---

## Imports and Exports

Reusable import/export infrastructure allows applications to implement data exchange consistently.

Typical use cases include:

* CSV imports
* Spreadsheet imports
* Data exports
* Bulk operations
* Integration pipelines

---

# Application Modules

djangospice is **not intended to be a standalone business application**.

Instead, it provides the runtime used by applications and modules.

For example:

```text
djangospice
    │
    ├── billing
    ├── notification
    ├── workflow
    ├── documents
    ├── helpdesk
    ├── CRM
    ├── workforce
    └── academic applications
```

Each application can depend on the common runtime while retaining responsibility for its own domain.

This keeps domain logic out of the framework.

---

# Example

A module can build its domain logic on top of djangospice:

```python
from djangospice.database.models import BaseModel


class Invoice(BaseModel):
    number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
```

The module can then use other djangospice infrastructure for events, notifications, UI, HTTP responses, tables, files, and other common functionality.

The result is a module that contains primarily **business/domain logic**, rather than infrastructure boilerplate.

---

# Philosophy

djangospice is not intended to replace Django.

It extends Django with a consistent application-runtime architecture.

```text
Django
   +
djangospice
   +
Application Modules
   =
Modular Django Application Ecosystem
```

Django remains responsible for the fundamental web framework capabilities.

djangospice provides the shared application infrastructure.

Individual modules provide the domain-specific functionality.

---

# Requirements

djangospice is built for modern Python and Django applications.

The exact supported versions should be defined by the project's package metadata.

---

# Development

Clone the repository:

```bash
git clone https://github.com/briansimpo/djangospice.git
cd djangospice
```

Create a development environment:

```bash
python -m venv .venv
```

Activate it:

### Linux / macOS

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

Install the package in editable mode:

```bash
pip install -e .
```

Install development dependencies if provided by the project:

```bash
pip install -e ".[dev]"
```

---

# Contributing

Contributions are welcome.

Before submitting a pull request:

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Add or update tests where appropriate.
5. Run the project's test suite.
6. Submit a pull request.

For larger changes, open an issue first so the proposed architecture can be discussed before implementation.

---

# Roadmap

djangospice is intended to evolve into a comprehensive runtime for modular Django applications.

Areas of development include:

* Application lifecycle management
* Module discovery and registration
* CLI tooling
* Event-driven application architecture
* Realtime communication
* Notification delivery
* UI/widget infrastructure
* HTMX integration
* Import/export pipelines
* File abstractions
* Background and asynchronous processing
* Application services
* Extensible registries
* Developer tooling

The framework will continue to favor **small, composable abstractions** over a large monolithic framework.

---

# Ecosystem

djangospice is intended to serve as the foundation for a broader ecosystem of reusable Django applications.

The ecosystem can be thought of as three layers:

### Runtime

**djangospice**

Provides shared infrastructure and application-runtime capabilities.

### Applications

Domain-specific Django applications built on top of the runtime.

Examples include:

* Billing
* CRM
* Workforce
* Workflow
* Documents
* Helpdesk
* Academic management

### Products

Complete products assembled from multiple applications.

This architecture allows the same application modules to be reused across different products.

---

# License

djangospice is licensed under the **MIT License**.

See [LICENSE](LICENSE) for the full license text.

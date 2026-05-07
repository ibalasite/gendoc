# EDD — Engineering Design Document

## §3.1 Domain Entities

```mermaid
classDiagram
    class User {
        +id: UUID
        +email: str
    }
    class Order
    class Product
    interface Repository
    enum OrderStatus
    abstract class BaseEntity
    class _PrivateImpl
```

## §3.2 Entity Tables

| Entity | Fields |
|--------|--------|
| User | id, email, name, created_at, updated_at |
| Order | id, user_id, status, total, items, paid_at |
| Product | id, name, price, stock |

## §4 REST API

GET /api/users
POST /api/users
PUT /api/users/{id}
DELETE /api/users/{id}

<<REST>> /orders

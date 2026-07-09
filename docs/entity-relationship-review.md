# Entity Relationship Review

来源：[classes_online_shopping_entities.puml](https://chatgpt.com/classes_online_shopping_entities.puml)

## 关系符号说明

| 符号   | 含义                           |
| ------ | ------------------------------ |
| `<|--` | 扩展 / 继承                    |
| `<|..` | 实现                           |
| `*--`  | 构成：没有整体就没有部分       |
| `o--`  | 聚合：部分可以独立于整体而存在 |
| `-->`  | 依赖性：对象使用另一个对象     |
| `..>`  | 依赖：较弱的依赖形式           |

## 待确认关系列表

| #    | PUML 关系                                             | 自然语言说明                                                 | 确认 | 注释                                                         |
| ---- | ----------------------------------------------------- | ------------------------------------------------------------ | ---- | ------------------------------------------------------------ |
| 1    | `Admin [1] *-- [1] Account`                           | `Admin` 拥有一个 `Account`，管理员账号是 `Admin` 身份的一部分。 | 1    | 整个平台只有一个 `Admin`。                                   |
| 2    | `Admin [1] --> [0..*] Shop`                           | `Admin` 使用/审核多个 `Shop`。                               | 1    | 平台管理员审核或管理店铺。                                   |
| 3    | `Admin [1] --> [0..*] Product`                        | `Admin` 使用/审核多个 `Product`。                            | 0    | 参考注释 1                                                   |
| 4    | `Customer [1] *-- [1] Account`                        | `Customer` 拥有一个 `Account`，客户账号是 `Customer` 身份的一部分。 | 1    |                                                              |
| 5    | `Catalog [1] ..> [0..*] Product`                      | `Catalog` 弱依赖 `Product`，用于按名称或分类搜索商品。       | 0    | 参考注释 2                                                   |
| 6    | `Account [1] o-- [0..1] CreditCard`                   | `Account` 可聚合一个 `CreditCard`，信用卡可以独立于账户存在。 | 1    |                                                              |
| 7    | `Account [1] o-- [0..1] ElectronicBankTransfer`       | `Account` 可聚合一个 `ElectronicBankTransfer`，银行转账信息可以独立于账户存在。 | 1    |                                                              |
| 8    | `Admin [1] o-- [0..*] Product`                        | `Admin` 聚合多个 `Product`，表示管理员可管理或审核商品集合。 | 0    | 参考注释 1                                                   |
| 9    | `Admin [1] o-- [0..*] ProductCategory`                | `Admin` 聚合多个 `ProductCategory`，表示管理员可管理或审核商品分类集合。 | 0    | 参考注释 2                                                   |
| 10   | `Customer [1] *-- [1] ShoppingCart`                   | `Customer` 拥有一个 `ShoppingCart`，购物车是客户购物流程的一部分。 | 1    |                                                              |
| 11   | `Customer [1] o-- [0..*] Order`                       | `Customer` 聚合多个 `Order`，订单可以作为历史记录独立存在。  | 1    |                                                              |
| 12   | `Customer [1] --> [0..*] Product`                     | `Customer` 使用 `Product`，例如评价商品时会引用商品。        | 0    | 参考注释 3                                                   |
| 13   | `Customer [1] ..> [0..*] ProductReview`               | `Customer` 弱依赖 `ProductReview`，例如创建商品评价。        | 0    | 参考注释 3                                                   |
| 14   | `Guest [1] ..> [1] Account`                           | `Guest` 弱依赖 `Account`，访客注册时会生成或接收账户。       | 1    |                                                              |
| 15   | `ShoppingCart [1] *-- [0..*] CartItem`                | `ShoppingCart` 由多个 `CartItem` 构成，购物车条目属于购物车内容。 | 1    |                                                              |
| 16   | `CartItem [1] --> [1] Product`                        | `CartItem` 使用一个 `Product`，表示购物车条目对应的商品。    | 0    | 购物车条目应指向具体 `ProductVariant`，而不是抽象的 `Product`。 |
| 17   | `CartItem [1] --> [1] ProductVariant`                 | `CartItem` 使用一个 `ProductVariant`，表示购物车条目对应的商品变体。 | 1    | 正确，购物车中保存的是具体规格/SKU。                         |
| 18   | `Order [1] *-- [0..*] OrderItem`                      | `Order` 由多个 `OrderItem` 构成，订单项属于订单内容。        | 1    |                                                              |
| 19   | `Order [1] *-- [0..*] OrderLog`                       | `Order` 由多个 `OrderLog` 构成，订单日志记录订单状态变化。   | 1    |                                                              |
| 20   | `Order [1] *-- [0..*] Shipment`                       | `Order` 由多个 `Shipment` 构成，发货信息属于订单履约过程。   | 1    | 一个订单可以拆分成多个发货包裹。                             |
| 21   | `Order [1] o-- [0..1] Payment`                        | `Order` 可聚合一个 `Payment`，支付记录可以独立于订单被处理或查询。 | 1    | 如果支持分期、补款、退款，可改成 `[0..*] Payment`。          |
| 22   | `OrderLog [1] o-- [0..*] Notification`                | `OrderLog` 聚合多个 `Notification`，用于记录订单状态通知。   | 0    | 通知不是订单日志的一部分，建议改为触发关系。                 |
| 23   | `Payment [1] o-- [0..1] PaymentMethod`                | `Payment` 可聚合一个 `PaymentMethod`，支付方式可以独立配置。 | 1    |                                                              |
| 24   | `Payment [1] *-- [0..1] PaymentTransaction`           | `Payment` 可由一个 `PaymentTransaction` 构成，交易记录属于该支付过程。 | 1    | 如果考虑支付重试、失败、退款，建议改成 `[0..*] PaymentTransaction`。 |
| 25   | `PaymentMethod [1] o-- [0..1] CreditCard`             | `PaymentMethod` 可聚合一个 `CreditCard`，用于信用卡支付方式。 | 1    |                                                              |
| 26   | `PaymentMethod [1] o-- [0..1] ElectronicBankTransfer` | `PaymentMethod` 可聚合一个 `ElectronicBankTransfer`，用于银行转账支付方式。 | 1    |                                                              |
| 27   | `Product [1] o-- [1] ProductCategory`                 | `Product` 聚合一个 `ProductCategory`，商品属于某个分类，分类可独立存在。 | 0    | 参考注释 2                                                   |
| 28   | `Product [1] *-- [0..*] ProductImage`                 | `Product` 由多个 `ProductImage` 构成，商品图片属于商品展示内容。 | 1    |                                                              |
| 29   | `Product [1] *-- [1..*] ProductVariant`               | `Product` 由一个或多个 `ProductVariant` 构成，商品变体属于商品。 | 1    | 商品至少有一个默认变体。                                     |
| 30   | `ProductReview [1] --> [1] Product`                   | `ProductReview` 使用一个 `Product`，表示评价针对的商品。     | 1    |                                                              |
| 31   | `Shipment [1] *-- [0..*] ShipmentLog`                 | `Shipment` 由多个 `ShipmentLog` 构成，发货日志属于发货过程。 | 1    |                                                              |
| 32   | `ShipmentLog [1] o-- [0..*] Notification`             | `ShipmentLog` 聚合多个 `Notification`，用于记录物流状态通知。 | 0    | 通知不是物流日志的一部分，建议改为触发关系。                 |
| 33   | `Manager [1] *-- [1] Account`                         | `Manager` 拥有一个 `Account`，店铺管理者账号是 `Manager` 身份的一部分。 | 1    |                                                              |
| 34   | `Manager [1] o-- [0..*] Shop`                         | `Manager` 聚合多个 `Shop`，表示一个店铺管理者可管理多个商店。 | 0    | 不建议用聚合，建议改成 `Manager --> Shop : manages`。        |
| 35   | `Manager [1] --> [0..*] Product`                      | `Manager` 使用多个 `Product`，用于向商店增删改查商品。       | 0    | 商品上架应通过 `ProductApproval`，不要让 `Manager` 直接把 `Product` 加入 `Shop`。 |
| 36   | `Shop [1] o-- [1] Manager`                            | `Shop` 聚合一个 `Manager`，表示商店由一个店铺管理者管理。    | 0    | 不建议用聚合，建议改成 `Shop --> Manager : managed by`。     |
| 37   | `Shop [1] o-- [0..1] Catalog`                         | `Shop` 可聚合一个 `Catalog`，商店目录可以独立于商店模型维护。 | 0    | 参考注释 2                                                   |
| 38   | `Shop [1] o-- [0..*] Product`                         | `Shop` 聚合多个 `Product`，表示商店中上架的商品集合。        | 1    | 但 `Product` 必须经过 `ProductApproval` 确认后才能加入 `Shop`。 |
| 39   | `Shop [1] o-- [0..*] ProductCategory`                 | `Shop` 聚合多个 `ProductCategory`，表示商店中使用的商品分类集合。 | 0    | 参考注释 2                                                   |
| 40   | `Admin [1] --> [0..*] Category`                       | `Admin` 管理多个 `Category`，包括增删改查分类。              | 1    | 替代原来的 `ProductCategory`。                               |
| 41   | `Category [0..*] o-- [0..*] Product`                  | `Category` 分类 `Product`，一个分类可包含多个商品，一个商品也可属于多个分类。 | 1    | 这里建议用 `o--`，不要写成 `o..`。                           |
| 42   | `Shop [1] --> [0..*] Category`                        | `Shop` 使用平台分类体系来组织商品。                          | 1    | 因为 `Category` 由 `Admin` 统一管理，所以 `Shop` 使用即可。  |
| 43   | `Manager [1] --> [0..*] Shop`                         | `Manager` 管理多个 `Shop`。                                  | 1    | 替代第 34 条。                                               |
| 44   | `Shop [1] --> [1] Manager`                            | `Shop` 由一个 `Manager` 管理。                               | 1    | 替代第 36 条。                                               |
| 45   | `Manager [1] --> [0..*] ProductApproval`              | `Manager` 提出或确认多个 `ProductApproval`。                 | 1    | 用于商品上架审批流程。                                       |
| 46   | `ProductApproval [1] *-- [1] Product`                 | `ProductApproval` 包含一个新添加的 `Product`。               | 1    | 该商品在审批确认前不应直接加入 `Shop`。                      |
| 47   | `ProductApproval [1] --> [1] Shop`                    | `ProductApproval` 指向目标 `Shop`，表示该商品申请添加到哪个商店。 | 1    |                                                              |
| 48   | `ProductApproval [1] --> [1] Manager`                 | `ProductApproval` 需要由 `Manager` 确认。                    | 1    | 可理解为 `confirmed by Manager`。                            |
| 49   | `OrderLog [1] --> [0..*] Notification`                | `OrderLog` 触发多个 `Notification`。                         | 1    | 替代第 22 条。                                               |
| 50   | `ShipmentLog [1] --> [0..*] Notification`             | `ShipmentLog` 触发多个 `Notification`。                      | 1    | 替代第 32 条。                                               |
| 51   | `Customer [1] o-- [0..*] ProductReview`               | `Customer` 聚合多个 `ProductReview`，表示客户写过的商品评价。 | 1    | 替代第 13 条。                                               |
| 52   | `OrderItem [1] --> [1] ProductVariant`                | `OrderItem` 使用一个 `ProductVariant`，表示订单项购买的具体商品变体。 | 1    | 订单项也应指向具体规格/SKU。                                 |

## 参考注释

### 参考注释 1：Admin 不直接管理 Product

`Admin` 主要负责平台级审核和管理，例如：

```plantuml
Admin [1] --> [0..*] Shop : reviews
Admin [1] --> [0..*] Category : manages
```

不建议使用：

```plantuml
Admin [1] --> [0..*] Product
Admin [1] o-- [0..*] Product
```

因为商品应由 `Manager` 通过 `ProductApproval` 添加到自己的 `Shop`。

------

### 参考注释 2：Catalog 和 ProductCategory 合并为 Category

删除：

```plantuml
Catalog
ProductCategory
```

替换为：

```plantuml
Category
```

对应关系改为：

```plantuml
Admin [1] --> [0..*] Category : manages
Category [0..*] o-- [0..*] Product : classifies
Shop [1] --> [0..*] Category : uses
```

------

### 参考注释 3：Customer 不直接依赖 Product / ProductReview

不建议使用：

```plantuml
Customer [1] --> [0..*] Product
Customer [1] ..> [0..*] ProductReview
```

建议改成：

```plantuml
Customer [1] o-- [0..*] ProductReview : writes
ProductReview [1] --> [1] Product : reviews
```

如果客户购买商品，应通过：

```plantuml
ShoppingCart [1] *-- [0..*] CartItem
CartItem [1] --> [1] ProductVariant

Order [1] *-- [0..*] OrderItem
OrderItem [1] --> [1] ProductVariant
```

------

## 最终建议加入的核心 PUML 关系

```plantuml
' Admin
Admin [1] *-- [1] Account
Admin [1] --> [0..*] Shop : reviews
Admin [1] --> [0..*] Category : manages

' Customer
Customer [1] *-- [1] Account
Customer [1] *-- [1] ShoppingCart
Customer [1] o-- [0..*] Order
Customer [1] o-- [0..*] ProductReview : writes

' Guest
Guest [1] ..> [1] Account : registers

' Account payment information
Account [1] o-- [0..1] CreditCard
Account [1] o-- [0..1] ElectronicBankTransfer

' Manager and Shop
Manager [1] *-- [1] Account
Manager [1] --> [0..*] Shop : manages
Shop [1] --> [1] Manager : managed by

' Category
Category [0..*] o-- [0..*] Product : classifies
Shop [1] --> [0..*] Category : uses

' Product approval
Manager [1] --> [0..*] ProductApproval : creates/confirms
ProductApproval [1] *-- [1] Product : contains
ProductApproval [1] --> [1] Shop : targets
ProductApproval [1] --> [1] Manager : confirmed by

' Product after approval
Shop [1] o-- [0..*] Product : lists
Product [1] *-- [0..*] ProductImage
Product [1] *-- [1..*] ProductVariant

' Shopping cart
ShoppingCart [1] *-- [0..*] CartItem
CartItem [1] --> [1] ProductVariant

' Order
Order [1] *-- [0..*] OrderItem
OrderItem [1] --> [1] ProductVariant
Order [1] *-- [0..*] OrderLog
Order [1] *-- [0..*] Shipment
Order [1] o-- [0..1] Payment

' Payment
Payment [1] o-- [0..1] PaymentMethod
Payment [1] *-- [0..1] PaymentTransaction
PaymentMethod [1] o-- [0..1] CreditCard
PaymentMethod [1] o-- [0..1] ElectronicBankTransfer

' Shipment and notification
Shipment [1] *-- [0..*] ShipmentLog
OrderLog [1] --> [0..*] Notification : triggers
ShipmentLog [1] --> [0..*] Notification : triggers

' Review
ProductReview [1] --> [1] Product : reviews
```

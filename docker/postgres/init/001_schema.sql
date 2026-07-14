CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Core account owned by Admin, Customer, and Manager domain entities.
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name VARCHAR(20) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'blocked', 'banned', 'compromised', 'archived', 'unknown')),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_country_code VARCHAR(16),
    phone_number VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);
CREATE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email);

CREATE TABLE IF NOT EXISTS addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    street VARCHAR(255) NOT NULL,
    city VARCHAR(120) NOT NULL,
    state VARCHAR(120) NOT NULL,
    postal_code VARCHAR(32) NOT NULL,
    country VARCHAR(120) NOT NULL,
    is_default_shipping BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_addresses_account ON addresses(account_id);

CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL UNIQUE REFERENCES accounts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS managers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL UNIQUE REFERENCES accounts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL UNIQUE REFERENCES accounts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS product_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL UNIQUE,
    slug VARCHAR(160) UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS catalogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(160) NOT NULL UNIQUE,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now(),
    product_names JSONB NOT NULL DEFAULT '{}'::jsonb,
    product_categories JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS shops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manager_id UUID NOT NULL REFERENCES managers(id) ON DELETE RESTRICT,
    name VARCHAR(160) NOT NULL UNIQUE,
    status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'rejected', 'suspended')),
    reviewed_by_admin_id UUID REFERENCES admins(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_shops_manager ON shops(manager_id);
CREATE INDEX IF NOT EXISTS idx_shops_status ON shops(status);

CREATE TABLE IF NOT EXISTS admin_shops (
    admin_id UUID NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
    shop_id UUID NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (admin_id, shop_id)
);

CREATE INDEX IF NOT EXISTS idx_admin_shops_shop ON admin_shops(shop_id);

CREATE TABLE IF NOT EXISTS admin_categories (
    admin_id UUID NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES product_categories(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (admin_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_admin_categories_category ON admin_categories(category_id);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_hash CHAR(64) NOT NULL UNIQUE,
    category_id UUID REFERENCES product_categories(id) ON DELETE SET NULL,
    name VARCHAR(160) NOT NULL UNIQUE,
    slug VARCHAR(200) NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    price NUMERIC(12, 2) NOT NULL CHECK (price > 0),
    available_item_count INTEGER NOT NULL DEFAULT 0 CHECK (available_item_count >= 0),
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);
CREATE INDEX IF NOT EXISTS idx_products_hash ON products(product_hash);

CREATE TABLE IF NOT EXISTS category_products (
    category_id UUID NOT NULL REFERENCES product_categories(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (category_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_category_products_product ON category_products(product_id);

CREATE TABLE IF NOT EXISTS catalog_products (
    catalog_id UUID NOT NULL REFERENCES catalogs(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (catalog_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_catalog_products_product ON catalog_products(product_id);

CREATE TABLE IF NOT EXISTS shop_products (
    shop_id UUID NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    added_by_manager_id UUID REFERENCES managers(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (shop_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_shop_products_product ON shop_products(product_id);

CREATE TABLE IF NOT EXISTS product_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_url VARCHAR(512) NOT NULL,
    rank INTEGER NOT NULL DEFAULT 0 CHECK (rank >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_product_images_product ON product_images(product_id);

CREATE TABLE IF NOT EXISTS product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_id_str VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    sku VARCHAR(64) NOT NULL UNIQUE,
    price NUMERIC(12, 2) NOT NULL CHECK (price > 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'cny',
    inventory_count INTEGER NOT NULL DEFAULT 0 CHECK (inventory_count >= 0),
    manages_inventory BOOLEAN NOT NULL DEFAULT true,
    allows_backorder BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_product_variants_product ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_product_variants_sku ON product_variants(sku);

CREATE TABLE IF NOT EXISTS product_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    shop_id UUID NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    manager_id UUID NOT NULL REFERENCES managers(id) ON DELETE RESTRICT,
    confirmed BOOLEAN NOT NULL DEFAULT false,
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (product_id, shop_id)
);

CREATE INDEX IF NOT EXISTS idx_product_approvals_shop ON product_approvals(shop_id);
CREATE INDEX IF NOT EXISTS idx_product_approvals_manager ON product_approvals(manager_id);
CREATE INDEX IF NOT EXISTS idx_product_approvals_confirmed ON product_approvals(confirmed);

CREATE TABLE IF NOT EXISTS shopping_carts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID UNIQUE REFERENCES customers(id) ON DELETE CASCADE,
    region_id VARCHAR(64),
    currency_code CHAR(3) NOT NULL DEFAULT 'cny',
    email VARCHAR(255),
    locale VARCHAR(16),
    shipping_address JSONB,
    billing_address JSONB,
    shipping_method JSONB,
    payment_session JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_shopping_carts_customer ON shopping_carts(customer_id);
CREATE INDEX IF NOT EXISTS idx_shopping_carts_email ON shopping_carts(email);

CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id UUID NOT NULL REFERENCES shopping_carts(id) ON DELETE CASCADE,
    product_variant_id UUID NOT NULL REFERENCES product_variants(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(12, 2) NOT NULL CHECK (price > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (cart_id, product_variant_id)
);

CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_variant ON cart_items(product_variant_id);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    order_number VARCHAR(64) NOT NULL UNIQUE,
    display_order_id VARCHAR(64) UNIQUE,
    status VARCHAR(32) NOT NULL DEFAULT 'created'
        CHECK (status IN ('created', 'confirmed', 'processing', 'shipped', 'completed', 'canceled', 'pending')),
    refund_status VARCHAR(32) NOT NULL DEFAULT 'none'
        CHECK (refund_status IN ('none', 'requested', 'approved', 'rejected', 'refunded')),
    email VARCHAR(255),
    region_id VARCHAR(64),
    currency_code CHAR(3) NOT NULL DEFAULT 'cny',
    shipping_address JSONB,
    billing_address JSONB,
    shipping_method JSONB,
    cart_id UUID,
    order_access_token VARCHAR(128),
    order_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orders_account ON orders(account_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    product_name VARCHAR(160) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(12, 2) NOT NULL CHECK (price > 0),
    shop_id UUID REFERENCES shops(id) ON DELETE SET NULL,
    shop_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_variant ON order_items(product_variant_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);

CREATE TABLE IF NOT EXISTS order_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL
        CHECK (status IN ('created', 'confirmed', 'processing', 'shipped', 'completed', 'canceled')),
    creation_date TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_order_logs_order ON order_logs(order_id);

CREATE TABLE IF NOT EXISTS payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    method_type VARCHAR(64) NOT NULL
        CHECK (method_type IN ('credit_card', 'electronic_bank_transfer')),
    is_default BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payment_methods_account ON payment_methods(account_id);

CREATE TABLE IF NOT EXISTS credit_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_method_id UUID NOT NULL UNIQUE REFERENCES payment_methods(id) ON DELETE CASCADE,
    name_on_card VARCHAR(200) NOT NULL,
    card_number_hash TEXT NOT NULL,
    security_code_hash TEXT,
    billing_street VARCHAR(255) NOT NULL,
    billing_city VARCHAR(120) NOT NULL,
    billing_state VARCHAR(120) NOT NULL,
    billing_postal_code VARCHAR(32) NOT NULL,
    billing_country VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS electronic_bank_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_method_id UUID NOT NULL UNIQUE REFERENCES payment_methods(id) ON DELETE CASCADE,
    bank_name VARCHAR(160) NOT NULL,
    routing_number_hash TEXT NOT NULL,
    account_number_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    payment_method_id UUID REFERENCES payment_methods(id) ON DELETE SET NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('unpaid', 'pending', 'completed', 'failed', 'declined', 'canceled', 'abandoned', 'settling', 'settled', 'refunded')),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL DEFAULT 'CNY',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_method ON payments(payment_method_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    transaction_id VARCHAR(160) UNIQUE,
    provider VARCHAR(120),
    status VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('unpaid', 'pending', 'completed', 'failed', 'declined', 'canceled', 'abandoned', 'settling', 'settled', 'refunded')),
    created_on TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payment_transactions_payment ON payment_transactions(payment_id);

CREATE TABLE IF NOT EXISTS shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    shop_id UUID REFERENCES shops(id) ON DELETE SET NULL,
    shipment_date TIMESTAMPTZ NOT NULL,
    estimated_arrival TIMESTAMPTZ NOT NULL,
    shipment_method VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_shipments_order ON shipments(order_id);

CREATE TABLE IF NOT EXISTS shipment_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL
        CHECK (status IN ('pending', 'shipped', 'delivered', 'on_hold')),
    creation_date TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_shipment_logs_shipment ON shipment_logs(shipment_id);

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(32) NOT NULL CHECK (channel IN ('email', 'sms')),
    receiver VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_on TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_receiver ON notifications(receiver);
CREATE INDEX IF NOT EXISTS idx_notifications_channel ON notifications(channel);

CREATE TABLE IF NOT EXISTS order_log_notifications (
    order_log_id UUID NOT NULL REFERENCES order_logs(id) ON DELETE CASCADE,
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (order_log_id, notification_id)
);

CREATE TABLE IF NOT EXISTS shipment_log_notifications (
    shipment_log_id UUID NOT NULL REFERENCES shipment_logs(id) ON DELETE CASCADE,
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (shipment_log_id, notification_id)
);

CREATE TABLE IF NOT EXISTS product_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_product_reviews_customer ON product_reviews(customer_id);
CREATE INDEX IF NOT EXISTS idx_product_reviews_product ON product_reviews(product_id);

-- Recommendation system tables
CREATE TABLE IF NOT EXISTS user_behavior_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(64) NOT NULL,
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    anonymous_id VARCHAR(128),
    session_id VARCHAR(128),
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    product_name VARCHAR(200),
    product_slug VARCHAR(200),
    shop_id UUID REFERENCES shops(id) ON DELETE SET NULL,
    shop_name VARCHAR(200),
    category_id UUID REFERENCES product_categories(id) ON DELETE SET NULL,
    category_name VARCHAR(200),
    query VARCHAR(500),
    quantity INTEGER,
    price FLOAT,
    source_page VARCHAR(500),
    metadata_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ube_account ON user_behavior_events(account_id);
CREATE INDEX IF NOT EXISTS idx_ube_anon ON user_behavior_events(anonymous_id);
CREATE INDEX IF NOT EXISTS idx_ube_session ON user_behavior_events(session_id);
CREATE INDEX IF NOT EXISTS idx_ube_type ON user_behavior_events(event_type);
CREATE INDEX IF NOT EXISTS idx_ube_product ON user_behavior_events(product_id);
CREATE INDEX IF NOT EXISTS idx_ube_shop ON user_behavior_events(shop_id);
CREATE INDEX IF NOT EXISTS idx_ube_created ON user_behavior_events(created_at);
CREATE INDEX IF NOT EXISTS idx_ube_type_product_time ON user_behavior_events(event_type, product_id, created_at);

CREATE TABLE IF NOT EXISTS recommendation_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    recommended_product_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    reason VARCHAR(500),
    reason_type VARCHAR(32) NOT NULL DEFAULT 'rule_based',
    score FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_rec_cache_product ON recommendation_cache(product_id);
CREATE INDEX IF NOT EXISTS idx_rec_cache_type ON recommendation_cache(reason_type);

DO $$
DECLARE
    table_name text;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'accounts',
        'addresses',
        'admins',
        'managers',
        'customers',
        'product_categories',
        'catalogs',
        'shops',
        'products',
        'shop_products',
        'product_variants',
        'product_approvals',
        'shopping_carts',
        'cart_items',
        'orders',
        'payment_methods',
        'credit_cards',
        'electronic_bank_transfers',
        'payments',
        'shipments',
        'product_reviews',
        'user_behavior_events',
        'recommendation_cache'
    ]
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_%I_updated_at ON %I', table_name, table_name);
        EXECUTE format(
            'CREATE TRIGGER trg_%I_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION set_updated_at()',
            table_name,
            table_name
        );
    END LOOP;
END $$;

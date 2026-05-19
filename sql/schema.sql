create extension if not exists pgcrypto;

create table if not exists products (
    id uuid primary key default gen_random_uuid(),
    sku text unique not null,
    product_name text not null,
    category text default 'Shoes',
    brand_name text,
    gender text,
    size text not null,
    color text not null,
    base_price numeric not null,
    discount_price numeric,
    currency text default 'INR',
    status text default 'Active',
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists inventory (
    id uuid primary key default gen_random_uuid(),
    product_id uuid references products(id) on delete cascade,
    sku text unique not null,
    warehouse_location text default 'Main Warehouse',
    available_quantity int default 0,
    reserved_quantity int default 0,
    sold_quantity int default 0,
    reorder_level int default 5,
    inventory_status text default 'In Stock',
    last_updated_at timestamptz default now()
);

create table if not exists customers (
    id uuid primary key default gen_random_uuid(),
    customer_name text not null,
    email text,
    phone text,
    city text,
    customer_type text default 'Retail',
    customer_level text default 'New Lead',
    source text,
    assigned_sales_owner text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists customer_status (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid references customers(id) on delete cascade,
    current_stage text default 'New Lead',
    latest_update text,
    next_action text,
    next_action_date date,
    quotation_requested boolean default false,
    quotation_sent boolean default false,
    quotation_sent_at timestamptz,
    last_contacted_at timestamptz,
    status_owner text,
    priority text default 'Medium',
    updated_at timestamptz default now(),
    unique (customer_id)
);

create table if not exists customer_activities (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid references customers(id) on delete cascade,
    activity_type text not null,
    activity_message text not null,
    related_entity_type text,
    related_entity_id uuid,
    created_by text default 'System',
    created_at timestamptz default now()
);

create table if not exists quotations (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid references customers(id) on delete cascade,
    quotation_number text unique not null,
    quotation_status text default 'Draft',
    total_amount numeric default 0,
    discount_amount numeric default 0,
    final_amount numeric default 0,
    valid_until date,
    sent_to_customer boolean default false,
    sent_at timestamptz,
    created_by text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists quotation_items (
    id uuid primary key default gen_random_uuid(),
    quotation_id uuid references quotations(id) on delete cascade,
    product_id uuid references products(id),
    sku text not null,
    product_name text,
    size text,
    color text,
    quantity int not null,
    unit_price numeric not null,
    line_total numeric not null
);

create table if not exists orders (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid references customers(id) on delete cascade,
    quotation_id uuid references quotations(id),
    order_number text unique not null,
    order_status text default 'Created',
    payment_status text default 'Pending',
    fulfillment_status text default 'Pending',
    shipment_status text default 'Not Shipped',
    total_amount numeric default 0,
    delivery_city text,
    latest_update text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists order_items (
    id uuid primary key default gen_random_uuid(),
    order_id uuid references orders(id) on delete cascade,
    product_id uuid references products(id),
    sku text not null,
    quantity int not null,
    unit_price numeric not null,
    line_total numeric not null
);

create table if not exists maestro_processes (
    id uuid primary key default gen_random_uuid(),
    maestro_instance_id text unique not null,
    customer_id uuid references customers(id),
    order_id uuid references orders(id),
    quotation_id uuid references quotations(id),
    process_type text default 'Shoe Order Flow',
    current_step text,
    process_status text default 'Running',
    exception_flag boolean default false,
    last_error text,
    started_at timestamptz default now(),
    completed_at timestamptz
);

create index if not exists idx_products_sku on products(sku);
create index if not exists idx_inventory_sku on inventory(sku);
create index if not exists idx_customers_email on customers(email);
create index if not exists idx_customers_phone on customers(phone);
create index if not exists idx_quotations_customer_id on quotations(customer_id);
create index if not exists idx_orders_customer_id on orders(customer_id);
create index if not exists idx_maestro_processes_instance_id on maestro_processes(maestro_instance_id);
create index if not exists idx_customer_activities_customer_id on customer_activities(customer_id);
create index if not exists idx_customer_activities_created_at on customer_activities(created_at);

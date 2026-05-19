insert into products (sku, product_name, category, brand_name, gender, size, color, base_price, discount_price, currency, status)
values
    ('RUNX-BLK-09', 'RunnerX Pro', 'Running Shoes', 'ShoeBrand', 'Men', 'UK 9', 'Black', 3499, 2999, 'INR', 'Active'),
    ('RUNX-WHT-08', 'RunnerX Pro', 'Running Shoes', 'ShoeBrand', 'Men', 'UK 8', 'White', 3499, 2999, 'INR', 'Active'),
    ('STRF-BLU-07', 'StreetFlex', 'Casual Shoes', 'ShoeBrand', 'Unisex', 'UK 7', 'Blue', 2499, 2199, 'INR', 'Active'),
    ('AIRL-GRY-06', 'AirLite Walk', 'Walking Shoes', 'ShoeBrand', 'Women', 'UK 6', 'Grey', 2999, 2599, 'INR', 'Active'),
    ('TRKB-BRN-10', 'TrekBoot Max', 'Boots', 'ShoeBrand', 'Men', 'UK 10', 'Brown', 4999, 4499, 'INR', 'Active')
on conflict (sku) do update set
    product_name = excluded.product_name,
    category = excluded.category,
    brand_name = excluded.brand_name,
    gender = excluded.gender,
    size = excluded.size,
    color = excluded.color,
    base_price = excluded.base_price,
    discount_price = excluded.discount_price,
    currency = excluded.currency,
    status = excluded.status,
    updated_at = now();

insert into inventory (product_id, sku, available_quantity, reserved_quantity, sold_quantity, reorder_level, inventory_status)
values
    ((select id from products where sku = 'RUNX-BLK-09'), 'RUNX-BLK-09', 25, 0, 0, 5, 'In Stock'),
    ((select id from products where sku = 'RUNX-WHT-08'), 'RUNX-WHT-08', 0, 0, 0, 5, 'Out of Stock'),
    ((select id from products where sku = 'STRF-BLU-07'), 'STRF-BLU-07', 12, 0, 0, 5, 'In Stock'),
    ((select id from products where sku = 'AIRL-GRY-06'), 'AIRL-GRY-06', 8, 0, 0, 5, 'In Stock'),
    ((select id from products where sku = 'TRKB-BRN-10'), 'TRKB-BRN-10', 3, 0, 0, 5, 'Low Stock')
on conflict (sku) do update set
    product_id = excluded.product_id,
    available_quantity = excluded.available_quantity,
    reserved_quantity = excluded.reserved_quantity,
    sold_quantity = excluded.sold_quantity,
    reorder_level = excluded.reorder_level,
    inventory_status = excluded.inventory_status,
    last_updated_at = now();

insert into customers (customer_name, email, phone, city, customer_type, customer_level, source, assigned_sales_owner)
values
    ('Rohan Sharma', 'rohan.sharma@example.com', '+919876543210', 'Mumbai', 'Retail', 'Quotation Sent', 'Website', 'Anika Rao'),
    ('Sneha Iyer', 'sneha.iyer@example.com', '+919812345678', 'Bengaluru', 'Retail', 'New Lead', 'Instagram', 'Vikram Mehta')
on conflict do nothing;

insert into customer_status (customer_id, current_stage, latest_update, next_action, quotation_requested, quotation_sent, status_owner, priority)
select id, 'Quotation Sent', 'Quotation QT-2026-001 was sent to customer.', 'Follow up with customer', true, true, 'Anika Rao', 'High'
from customers where email = 'rohan.sharma@example.com'
on conflict (customer_id) do update set
    current_stage = excluded.current_stage,
    latest_update = excluded.latest_update,
    next_action = excluded.next_action,
    quotation_requested = excluded.quotation_requested,
    quotation_sent = excluded.quotation_sent,
    status_owner = excluded.status_owner,
    priority = excluded.priority,
    updated_at = now();

insert into customer_status (customer_id, current_stage, latest_update, next_action, quotation_requested, quotation_sent, status_owner, priority)
select id, 'New Lead', 'Customer asked about RunnerX Pro availability.', 'Share product options', false, false, 'Vikram Mehta', 'Medium'
from customers where email = 'sneha.iyer@example.com'
on conflict (customer_id) do update set
    current_stage = excluded.current_stage,
    latest_update = excluded.latest_update,
    next_action = excluded.next_action,
    quotation_requested = excluded.quotation_requested,
    quotation_sent = excluded.quotation_sent,
    status_owner = excluded.status_owner,
    priority = excluded.priority,
    updated_at = now();

insert into customer_activities (customer_id, activity_type, activity_message, created_by)
select id, 'Customer Created', 'Customer Rohan Sharma was created.', 'Seed'
from customers where email = 'rohan.sharma@example.com'
union all
select id, 'Quotation Sent', 'Quotation QT-2026-001 was sent to customer.', 'Seed'
from customers where email = 'rohan.sharma@example.com'
union all
select id, 'Customer Created', 'Customer Sneha Iyer was created.', 'Seed'
from customers where email = 'sneha.iyer@example.com';

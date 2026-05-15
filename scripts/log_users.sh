#!/bin/bash
# Script to log the users table from the database

echo "========================================"
echo "USERS TABLE LOG"
echo "========================================"
echo ""

# Run the SQL query inside the Docker container
docker-compose exec postgres psql -U postgres -d seo_lens -c "
SELECT 
    id,
    email,
    full_name,
    role,
    is_active,
    created_at
FROM users 
ORDER BY created_at DESC;
"

echo ""
echo "========================================"
echo "TOTAL USERS:"
docker-compose exec postgres psql -U postgres -d seo_lens -c "SELECT COUNT(*) FROM users;"
echo "========================================"

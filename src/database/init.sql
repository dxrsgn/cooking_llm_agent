/* some dummies to prepopulate data */
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    login VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    last_queries JSON DEFAULT '[]',
    preferences JSON DEFAULT '[]',
    allergies JSON DEFAULT '[]'
);

INSERT INTO users (login, password) VALUES
    ('user1', 'password1'),
    ('user2', 'password2')
ON CONFLICT (login) DO NOTHING;

INSERT INTO user_profiles (user_id, last_queries, preferences, allergies)
SELECT id, '[]', '["italian", "spicy"]', '["peanuts"]'
FROM users WHERE login = 'user1'
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_profiles (user_id, last_queries, preferences, allergies)
SELECT id, '[]', '["vegan"]', '["shellfish"]'
FROM users WHERE login = 'user2'
ON CONFLICT (user_id) DO NOTHING;

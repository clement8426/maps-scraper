-- ============================================================
-- 🔍 Requêtes SQL de diagnostic pour comprendre les IDs
-- ============================================================

-- 1️⃣ Voir les IDs MIN et MAX de la base
SELECT 
    MIN(id) as premier_id,
    MAX(id) as dernier_id,
    COUNT(*) as total_entreprises
FROM companies;

-- 2️⃣ Voir les 10 premières entreprises (IDs les plus anciens)
SELECT id, company_name, city, website, osint_status, updated_at
FROM companies
ORDER BY id ASC
LIMIT 10;

-- 3️⃣ Voir les 10 dernières entreprises (IDs les plus récents)
SELECT id, company_name, city, website, osint_status, updated_at
FROM companies
ORDER BY id DESC
LIMIT 10;

-- 4️⃣ Compter les entreprises par statut OSINT
SELECT 
    osint_status,
    COUNT(*) as nombre
FROM companies
GROUP BY osint_status
ORDER BY nombre DESC;

-- 5️⃣ Voir les entreprises à enrichir (comme le pipeline)
SELECT id, company_name, city, website, osint_status
FROM companies
WHERE (osint_status IS NULL OR osint_status NOT IN ('Done','Skipped'))
  AND website IS NOT NULL 
  AND website <> ''
ORDER BY id ASC
LIMIT 10;

-- 6️⃣ Chercher un ID spécifique (remplacer 41971 par l'ID recherché)
SELECT id, company_name, city, website, osint_status, created_at, updated_at
FROM companies
WHERE id = 41971;

-- 7️⃣ Voir les IDs qui ont des "trous" (IDs manquants)
-- Cette requête vérifie si les IDs sont consécutifs
SELECT 
    t1.id as id_actuel,
    t1.id + 1 as id_suivant_attendu,
    MIN(t2.id) as id_suivant_reel,
    CASE 
        WHEN MIN(t2.id) - t1.id > 1 THEN 'TROU DETECTE'
        ELSE 'OK'
    END as statut
FROM companies t1
LEFT JOIN companies t2 ON t2.id > t1.id
GROUP BY t1.id
HAVING MIN(t2.id) - t1.id > 1 OR MIN(t2.id) IS NULL
LIMIT 20;

-- 8️⃣ Voir les entreprises de La Chaux-de-Fonds à enrichir
SELECT id, company_name, website, osint_status
FROM companies
WHERE city = 'La Chaux-de-Fonds'
  AND (osint_status IS NULL OR osint_status NOT IN ('Done','Skipped'))
  AND website IS NOT NULL 
  AND website <> ''
ORDER BY id ASC
LIMIT 20;

-- 9️⃣ Statistiques par ville
SELECT 
    city,
    COUNT(*) as total,
    SUM(CASE WHEN osint_status = 'Done' THEN 1 ELSE 0 END) as enrichies,
    SUM(CASE WHEN osint_status IS NULL THEN 1 ELSE 0 END) as a_enrichir
FROM companies
WHERE website IS NOT NULL AND website <> ''
GROUP BY city
ORDER BY total DESC;

-- 🔟 Voir les dernières modifications (triées par updated_at)
SELECT id, company_name, city, osint_status, updated_at
FROM companies
ORDER BY updated_at DESC
LIMIT 10;


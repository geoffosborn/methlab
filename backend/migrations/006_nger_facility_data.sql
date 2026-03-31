-- Map NGER Safeguard Mechanism data to facilities
-- Source: Clean Energy Regulator 2023-24 Baselines and Emissions Table
-- https://cer.gov.au/document/2023-24-baselines-and-emissions-table

-- Update nger_id (using responsible emitter ABN as identifier) and add baseline/emissions metadata
-- Format: nger_id = "NGER-<ABN>" to create a stable identifier

-- QLD - Bowen Basin
UPDATE facilities SET nger_id = 'NGER-MoranNth', metadata = jsonb_build_object(
  'nger_name', 'Moranbah North Mine', 'nger_emitter', 'ANGLO COAL (MORANBAH NORTH MANAGEMENT) PTY LIMITED',
  'nger_baseline_2024', 1300300, 'nger_reported_2024', 1483999
) WHERE name = 'Moranbah North' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Grosvenor', metadata = jsonb_build_object(
  'nger_name', 'Grosvenor Mine', 'nger_emitter', 'ANGLO COAL (MORANBAH NORTH MANAGEMENT) PTY LIMITED',
  'nger_baseline_2024', 1717249, 'nger_reported_2024', 1094252
) WHERE name = 'Grosvenor' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Capcoal', metadata = jsonb_build_object(
  'nger_name', 'Capcoal Mine', 'nger_emitter', 'ANGLO COAL (CAPCOAL MANAGEMENT) PTY LIMITED',
  'nger_baseline_2024', 2070902, 'nger_reported_2024', 1048254
) WHERE name = 'Capcoal (Aquila)' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Dawson', metadata = jsonb_build_object(
  'nger_name', 'Dawson Mine', 'nger_emitter', 'ANGLO COAL (DAWSON MANAGEMENT) PTY LTD',
  'nger_baseline_2024', 485823, 'nger_reported_2024', 538741
) WHERE name = 'Dawson' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-HailCreek', metadata = jsonb_build_object(
  'nger_name', 'Hail Creek Mine', 'nger_emitter', 'HAIL CREEK COAL PTY LTD',
  'nger_baseline_2024', 1189092, 'nger_reported_2024', 1381195
) WHERE name = 'Hail Creek' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-GoonyBroad', metadata = jsonb_build_object(
  'nger_name', 'Goonyella Broadmeadow Mine', 'nger_emitter', 'BM Alliance Coal Operations Pty Limited',
  'nger_baseline_2024', 1015171, 'nger_reported_2024', 1257022
) WHERE name = 'Goonyella Riverside' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-PeakDowns', metadata = jsonb_build_object(
  'nger_name', 'Peak Downs Mine', 'nger_emitter', 'BM Alliance Coal Operations Pty Limited',
  'nger_baseline_2024', 371336, 'nger_reported_2024', 434812
) WHERE name = 'Peak Downs' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Saraji', metadata = jsonb_build_object(
  'nger_name', 'Saraji Mine', 'nger_emitter', 'BM Alliance Coal Operations Pty Limited',
  'nger_baseline_2024', 311441, 'nger_reported_2024', 353611
) WHERE name = 'Saraji' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-CavalRidge', metadata = jsonb_build_object(
  'nger_name', 'Caval Ridge Mine', 'nger_emitter', 'BM Alliance Coal Operations Pty Limited',
  'nger_baseline_2024', 177734, 'nger_reported_2024', 161798
) WHERE name = 'Caval Ridge' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Daunia', metadata = jsonb_build_object(
  'nger_name', 'Daunia Mine', 'nger_emitter', 'BM Alliance Coal Operations Pty Limited / WHITEHAVEN DAUNIA PTY LTD',
  'nger_baseline_2024', 234840, 'nger_reported_2024', 215551
) WHERE name = 'Daunia' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Blackwater', metadata = jsonb_build_object(
  'nger_name', 'Blackwater Mine', 'nger_emitter', 'BM Alliance Coal Operations / WHITEHAVEN BLACKWATER PTY LTD',
  'nger_baseline_2024', 641861, 'nger_reported_2024', 722053
) WHERE name = 'Blackwater' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-SWalkerCk', metadata = jsonb_build_object(
  'nger_name', 'South Walker Creek', 'nger_emitter', 'STANMORE RESOURCES LIMITED',
  'nger_baseline_2024', 382706, 'nger_reported_2024', 474299
) WHERE name = 'South Walker Creek' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Poitrel', metadata = jsonb_build_object(
  'nger_name', 'Poitrel Mine', 'nger_emitter', 'STANMORE RESOURCES LIMITED',
  'nger_baseline_2024', 215485, 'nger_reported_2024', 298489
) WHERE name = 'Poitrel' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Curragh', metadata = jsonb_build_object(
  'nger_name', 'Curragh Mine', 'nger_emitter', 'CORONADO AUSTRALIA HOLDINGS PTY LTD',
  'nger_baseline_2024', 598727, 'nger_reported_2024', 909433
) WHERE name = 'Curragh' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-OakyCreek', metadata = jsonb_build_object(
  'nger_name', 'Oaky Creek Coal Complex', 'nger_emitter', 'OAKY CREEK HOLDINGS PTY LIMITED',
  'nger_baseline_2024', 759605, 'nger_reported_2024', 845959
) WHERE name = 'Oaky Creek' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Rolleston', metadata = jsonb_build_object(
  'nger_name', 'Rolleston Coal Mine', 'nger_emitter', 'ROLLESTON COAL HOLDINGS PTY LIMITED',
  'nger_baseline_2024', 164679, 'nger_reported_2024', 173698
) WHERE name = 'Rolleston' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Clermont', metadata = jsonb_build_object(
  'nger_name', 'Clermont Coal Operations', 'nger_emitter', 'Clermont Coal Operations Pty Limited',
  'nger_baseline_2024', 170356, 'nger_reported_2024', 148835
) WHERE name = 'Clermont' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Collinsvl', metadata = jsonb_build_object(
  'nger_name', 'Collinsville Mine', 'nger_emitter', 'NC COAL COMPANY PTY LIMITED',
  'nger_baseline_2024', 100000, 'nger_reported_2024', 69982
) WHERE name = 'Collinsville' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Coppabella', metadata = jsonb_build_object(
  'nger_name', 'Coppabella Coal Mine', 'nger_emitter', 'PEABODY ENERGY AUSTRALIA PCI (C&M MANAGEMENT) PTY LTD',
  'nger_baseline_2024', 219678, 'nger_reported_2024', 235397
) WHERE name = 'Coppabella' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Moorvale', metadata = jsonb_build_object(
  'nger_name', 'Moorvale Coal Mine', 'nger_emitter', 'PEABODY ENERGY AUSTRALIA PCI (C&M MANAGEMENT) PTY LTD',
  'nger_baseline_2024', 221575, 'nger_reported_2024', 194654
) WHERE name = 'Moorvale' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Middlmnt', metadata = jsonb_build_object(
  'nger_name', 'Middlemount Coal Mine', 'nger_emitter', 'Middlemount Coal Pty Ltd',
  'nger_baseline_2024', 232430, 'nger_reported_2024', 267919
) WHERE name = 'Middlemount' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-IsaacPlns', metadata = jsonb_build_object(
  'nger_name', 'Isaac Plains Complex', 'nger_emitter', 'STANMORE RESOURCES LIMITED',
  'nger_baseline_2024', 167250, 'nger_reported_2024', 202682
) WHERE name = 'Isaac Plains' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Foxleigh', metadata = jsonb_build_object(
  'nger_name', 'Foxleigh Mine', 'nger_emitter', 'FOXLEIGH MANAGEMENT PTY LTD',
  'nger_baseline_2024', 215614, 'nger_reported_2024', 265558
) WHERE name = 'Foxleigh' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Jellinbah', metadata = jsonb_build_object(
  'nger_name', 'Jellinbah Mine', 'nger_emitter', 'JELLINBAH MINING PTY LTD',
  'nger_baseline_2024', 321854, 'nger_reported_2024', 364464
) WHERE name = 'Jellinbah' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-CarbDns', metadata = jsonb_build_object(
  'nger_name', 'Carborough Downs Coal Mine', 'nger_emitter', 'FITZROY (CQ) PTY LTD',
  'nger_baseline_2024', 419085, 'nger_reported_2024', 589348
) WHERE name = 'Carborough Downs' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Burton', metadata = jsonb_build_object(
  'nger_name', 'Burton Complex', 'nger_emitter', 'BOWEN COKING COAL LIMITED',
  'nger_baseline_2024', 165342, 'nger_reported_2024', 167954
) WHERE name = 'Burton' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Kestrel', metadata = jsonb_build_object(
  'nger_name', 'Kestrel Coal Pty Ltd', 'nger_emitter', 'Kestrel Coal Group Pty Ltd',
  'nger_baseline_2024', 1035251, 'nger_reported_2024', 1223730
) WHERE name = 'Kestrel' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Ensham', metadata = jsonb_build_object(
  'nger_name', 'Ensham Coal Mine', 'nger_emitter', 'ENSHAM RESOURCES PTY. LIMITED',
  'nger_baseline_2024', 272747, 'nger_reported_2024', 254139
) WHERE name = 'Ensham' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Yarrabee', metadata = jsonb_build_object(
  'nger_name', 'Yarrabee Coal Mine (Open Cut)', 'nger_emitter', 'YARRABEE COAL COMPANY PTY. LTD.',
  'nger_baseline_2024', 136622, 'nger_reported_2024', 183809
) WHERE name = 'Yarrabee' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-GregCrin', metadata = jsonb_build_object(
  'nger_name', 'Sojitz Gregory Crinum Mine', 'nger_emitter', 'SOJITZ DEVELOPMENT PTY LTD',
  'nger_baseline_2024', 102951, 'nger_reported_2024', 65978
) WHERE name = 'Gregory Crinum' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Byerwen', metadata = jsonb_build_object(
  'nger_name', 'Byerwen Mine', 'nger_emitter', 'BYERWEN COAL PTY LTD',
  'nger_baseline_2024', 360395, 'nger_reported_2024', 432031
) WHERE name = 'Byerwen' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-OliveDns', metadata = jsonb_build_object(
  'nger_name', 'Olive Downs Complex', 'nger_emitter', 'PEMBROKE RESOURCES NOMINEE PTY LTD',
  'nger_baseline_2024', 100000, 'nger_reported_2024', 155917
) WHERE name = 'Olive Downs' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-LakeVrmt', metadata = jsonb_build_object(
  'nger_name', 'Lake Vermont Mine', 'nger_emitter', 'THIESS PTY LTD',
  'nger_baseline_2024', 308609, 'nger_reported_2024', 289068
) WHERE name = 'Lake Vermont' AND state = 'QLD';

UPDATE facilities SET nger_id = 'NGER-Cook', metadata = jsonb_build_object(
  'nger_name', 'Cook Colliery', 'nger_emitter', 'Constellation Mining Pty Ltd',
  'nger_baseline_2024', 100000, 'nger_reported_2024', 98801
) WHERE name = 'Cook' AND state = 'QLD';

-- NSW - Hunter Valley
UPDATE facilities SET nger_id = 'NGER-Bengalla', metadata = jsonb_build_object(
  'nger_name', 'Bengalla Operations', 'nger_emitter', 'Bengalla Mining Company Pty Limited',
  'nger_baseline_2024', 519270, 'nger_reported_2024', 626511
) WHERE name = 'Bengalla' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-HVOps', metadata = jsonb_build_object(
  'nger_name', 'Hunter Valley Operations mine', 'nger_emitter', 'HV OPERATIONS PTY LTD',
  'nger_baseline_2024', 491271, 'nger_reported_2024', 637147
) WHERE name = 'Hunter Valley Operations' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-MtPleasnt', metadata = jsonb_build_object(
  'nger_name', 'Mount Pleasant Operations', 'nger_emitter', 'MACH Energy Australia Pty Ltd',
  'nger_baseline_2024', 199238, 'nger_reported_2024', 196934
) WHERE name = 'Mount Pleasant' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Mangoola', metadata = jsonb_build_object(
  'nger_name', 'Mangoola', 'nger_emitter', 'MANGOOLA COAL OPERATIONS PTY LIMITED',
  'nger_baseline_2024', 131234, 'nger_reported_2024', 122216
) WHERE name = 'Mangoola' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Bulga', metadata = jsonb_build_object(
  'nger_name', 'Bulga Coal Complex', 'nger_emitter', 'BULGA COAL MANAGEMENT PTY LIMITED',
  'nger_baseline_2024', 656158, 'nger_reported_2024', 527889
) WHERE name = 'Bulga' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Integra', metadata = jsonb_build_object(
  'nger_name', 'Integra Underground Mine', 'nger_emitter', 'HV Coking Coal Pty Limited',
  'nger_baseline_2024', 322546, 'nger_reported_2024', 396320
) WHERE name = 'Integra' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Wambo', metadata = jsonb_build_object(
  'nger_name', 'Wambo Coal Mine', 'nger_emitter', 'WAMBO COAL PTY LIMITED',
  'nger_baseline_2024', 244508, 'nger_reported_2024', 162094
) WHERE name = 'Wambo' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Glendell', metadata = jsonb_build_object(
  'nger_name', 'Mt Owen Glendell Complex', 'nger_emitter', 'MT OWEN PTY LIMITED',
  'nger_baseline_2024', 206337, 'nger_reported_2024', 265669
) WHERE name = 'Glendell' AND state = 'NSW';

-- NSW - Gunnedah Basin
UPDATE facilities SET nger_id = 'NGER-MaulesCk', metadata = jsonb_build_object(
  'nger_name', 'Maules Creek Open Cut Mine', 'nger_emitter', 'MAULES CREEK COAL PTY LTD',
  'nger_baseline_2024', 275001, 'nger_reported_2024', 286028
) WHERE name = 'Maules Creek' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Narrabri', metadata = jsonb_build_object(
  'nger_name', 'Narrabri Underground Mine', 'nger_emitter', 'Narrabri Coal Operations Pty Ltd',
  'nger_baseline_2024', 383633, 'nger_reported_2024', 555048
) WHERE name = 'Narrabri' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Boggabri', metadata = jsonb_build_object(
  'nger_name', 'Boggabri Coal Minesite', 'nger_emitter', 'BOGGABRI COAL PTY LIMITED',
  'nger_baseline_2024', 206330, 'nger_reported_2024', 210390
) WHERE name = 'Boggabri' AND state = 'NSW';

-- NSW - Newcastle/Maitland
UPDATE facilities SET nger_id = 'NGER-Myuna', metadata = jsonb_build_object(
  'nger_name', 'Myuna Colliery', 'nger_emitter', 'CENTENNIAL MYUNA PTY LIMITED',
  'nger_baseline_2024', 346793, 'nger_reported_2024', 191750
) WHERE name = 'Myuna' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Mandalong', metadata = jsonb_build_object(
  'nger_name', 'Mandalong Mine', 'nger_emitter', 'CENTENNIAL MANDALONG PTY LIMITED',
  'nger_baseline_2024', 554933, 'nger_reported_2024', 742230
) WHERE name = 'Mandalong' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-ChainVly', metadata = jsonb_build_object(
  'nger_name', 'Chain Valley Colliery', 'nger_emitter', 'Delta Electricity Pty Ltd',
  'nger_baseline_2024', 588821, 'nger_reported_2024', 588821
) WHERE name = 'Chain Valley' AND state = 'NSW';

-- NSW - Illawarra
UPDATE facilities SET nger_id = 'NGER-Appin', metadata = jsonb_build_object(
  'nger_name', 'APN01 Appin Colliery - ICH Facility', 'nger_emitter', 'ENDEAVOUR COAL PTY LIMITED',
  'nger_baseline_2024', 2154439, 'nger_reported_2024', 1833982
) WHERE name = 'Appin' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Dendrobm', metadata = jsonb_build_object(
  'nger_name', 'DEN01', 'nger_emitter', 'Dendrobium Coal Pty Ltd',
  'nger_baseline_2024', 143922, 'nger_reported_2024', 379997
) WHERE name = 'Dendrobium' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-RussVale', metadata = jsonb_build_object(
  'nger_name', 'Russell Vale Colliery', 'nger_emitter', 'WOLLONGONG RESOURCES PTY. LTD.',
  'nger_baseline_2024', 110000, 'nger_reported_2024', 335908
) WHERE name = 'Russell Vale' AND state = 'NSW';

-- NSW - Other
UPDATE facilities SET nger_id = 'NGER-Moolarbn', metadata = jsonb_build_object(
  'nger_name', 'Moolarben Coal Mine (Open Cut & Underground)', 'nger_emitter', 'MOOLARBEN COAL OPERATIONS PTY LTD',
  'nger_baseline_2024', 238272, 'nger_reported_2024', 233663
) WHERE name = 'Moolarben' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Wilpnjng', metadata = jsonb_build_object(
  'nger_name', 'Wilpinjong Coal Mine', 'nger_emitter', 'WILPINJONG COAL PTY LTD',
  'nger_baseline_2024', 148354, 'nger_reported_2024', 162960
) WHERE name = 'Wilpinjong' AND state = 'NSW';

UPDATE facilities SET nger_id = 'NGER-Baralaba', metadata = jsonb_build_object(
  'nger_name', 'Baralaba Coal Mine', 'nger_emitter', 'BARALABA COAL COMPANY PTY LTD',
  'nger_baseline_2024', 142165, 'nger_reported_2024', 138324
) WHERE name = 'Baralaba' AND state = 'QLD';

-- WA
UPDATE facilities SET nger_id = 'NGER-ColliePr', metadata = jsonb_build_object(
  'nger_name', 'Premier Coal Mine (Open Cut)', 'nger_emitter', 'Premier Coal Pty Ltd',
  'nger_baseline_2024', 100000, 'nger_reported_2024', 110291
) WHERE name = 'Collie (Premier)' AND state = 'WA';

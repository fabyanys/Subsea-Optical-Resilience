# 08 - Crisis Scenario Simulation

Modul simulasi krisis telekomunikasi dan pemodelan topologi jaringan optik bawah laut UAE.

### Komponen:
1. `topologies/`:
   - `uae_subsea_cables.json`: Definisi graf kabel laut (landing stations, link antar-node, kapasitas total Gbps/Tbps, latency).
2. `scenarios/`:
   - `scenario_1_fujairah_cut.json`: Skenario putusnya kabel utama di stasiun pendaratan Fujairah.
   - `scenario_2_red_sea_chokepoint.json`: Gangguan pada koridor Laut Merah / Selat Bab-el-Mandeb.
   - `scenario_3_uae_banking_surge.json`: Lonjakan kebutuhan transaksi finansial saat kapasitas kabel terdegradasi.
3. `network_engine.py`:
   - Logika simulasi penghitungan rute terpendek (NetworkX), deteksi bottleneck, dan simulasi pengalihan rute (*rerouting*).

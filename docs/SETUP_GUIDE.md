# Ola Ride Insights – Setup & Run Guide

Ye guide `ola-ride-insights.zip` ko zero se chalane ke liye hai: **Part A** = zip mein kya hai + Python/SQL/Streamlit chalana, **Part B** = Power BI installation se leke Streamlit ke "Power BI Report" page pe report dikhne tak.

**Project:** OLA ride bookings (Bengaluru, July 2024, 103,024 rows) ka cleaning → EDA → SQL → Power BI dashboard → Streamlit app. Labmentrix deadline: 20 Nov 2026.

**Pehle se chahiye (Windows):**

| Cheez | Kyun | Check kaise kare |
| --- | --- | --- |
| Python 3.10+ | Cleaning, notebook, Streamlit | `python --version` |
| VS Code (Jupyter extension ke saath) | Notebook + terminal | VS Code kholo |
| Power BI Desktop (latest) | Dashboard | Part B, Step 1 |
| Git + GitHub account | Repo submit karna | `git --version` |
| Internet | Packages, vehicle icons, publish | — |

Notation: `code` wali lines terminal (VS Code ka PowerShell) mein type karni hain. Har command project folder ke andar se chalani hai.

## Part A1 — Zip ke andar kya-kya hai

Zip extract karne pe ek folder milega: `ola-ride-insights\`. Uske andar saari files ye hain:

| Folder / File | Kya hai | Kab use hoga |
| --- | --- | --- |
| `README.md` | GitHub ka front page: project summary, SQL results, insights, recommendations | GitHub pe dikhega |
| `requirements.txt` | Python packages ki list (pandas, numpy, openpyxl, matplotlib, seaborn, plotly, streamlit) | `pip install` ke time |
| `.gitignore` | Kaunsi files GitHub pe nahi jaani (ola.db, secrets.toml, cache) | Git push |
| `.git\` (hidden) | Git repo, commits already bane hue | GitHub push |
| `.streamlit\config.toml` | Streamlit ka Ola green theme | Apne aap load |
| `.streamlit\secrets.toml.example` | Power BI link save karne ka template | Part B, Step 12 |
| `data\raw\OLA_DataSet.xlsx` | Original dataset (sheet "July", 103,024 rows, 20 columns) | `clean.py` + notebook |
| `data\processed\ola_rides_clean.csv` | Cleaned data (32 columns) — Power BI aur Streamlit isi se chalte hain | Power BI, Streamlit |
| `data\processed\vehicle_types.csv` | 7 vehicle types + icon URL + sort order | Power BI table icons |
| `data\processed\ola.db` | SQLite database — zip mein nahi hai, `clean.py` ya app khud bana deta hai | SQL queries |
| `src\clean.py` | Cleaning script: raw xlsx → clean CSV + SQLite DB | Part A2, Step 4 |
| `notebooks\Ola_Ride_Insights_EDA.ipynb` | Teri template mein EDA: 15 charts, har chart ke 3 answers, summary, conclusion | Submit |
| `sql\01_schema_mysql.sql` | MySQL table banana + CSV load (optional) | Sirf MySQL chahiye to |
| `sql\02_ola_queries.sql` | Brief ke 10 questions (Q1–Q10) + 10 extra insight queries (X1–X10) | Submit + Streamlit |
| `app\app.py` | Streamlit app (Dashboard, SQL Query Explorer, Power BI Report, Insights) | Part A2, Step 6 |
| `assets\powerbi_screens\` | Khali folder — Power BI publish na ho paaye to page screenshots yahan daalo, app dikha dega | Part B, Plan B |
| `powerbi\OlaRideInsights.pbip` | Power BI project kholne wali file | Part B |
| `powerbi\OlaRideInsights.SemanticModel\` | Data model: 2 tables, relationship, 21 DAX measures, `DataFolder` parameter | Apne aap |
| `powerbi\OlaRideInsights.Report\` | 5 report pages, sab visuals, Ola backgrounds, theme | Apne aap |
| `docs\SETUP_GUIDE.md` | Yahi guide, text file mein | Offline reference |

**Cleaned data mein naye columns (notebook aur Power BI dono mein use hote hain):**

| Column | Matlab |
| --- | --- |
| `Booking_Datetime`, `Booking_Date`, `Booking_Time` | Date column ko tod ke banaye (purana `Time` hata diya, wo duplicate tha) |
| `Day`, `Day_Name`, `Weekday_Num`, `Is_Weekend`, `Hour`, `Time_Slot` | Time-based analysis ke liye |
| `Ride_Outcome` | Completed / Incomplete / Canceled by Customer / Canceled by Driver / Driver Not Found |
| `Is_Success`, `Is_Canceled` | 1/0 flags |
| `Revenue` | Booking value sirf successful rides ki, baaki 0 |
| `Distance_Band`, `Fare_per_km` | Distance groups + pricing anomaly check |

Missing values: text columns (cancel reasons, payment) mein `Not Applicable` bhara hai. Ratings aur TAT khaali (NULL) hi chhode hain, taaki averages galat na ho.

**Power BI ke 5 pages:**

| Page | Kya dikhata hai |
| --- | --- |
| Overall | 5 KPIs, Ride Volume Over Time, Booking Status Breakdown, Peak Demand by Hour |
| Vehicle Type | Vehicle scorecard table (icons ke saath), Top 5 Vehicle Types by Distance, Avg Distance |
| Revenue | Revenue by Payment Method, Top 5 Customers by Booking Value, Ride Distance per Day |
| Cancellation | Customer reasons, Driver reasons, Cancellations by Vehicle |
| Ratings | Driver ratings distribution, Customer ratings distribution, Customer vs Driver by Vehicle |

Har page pe left nav buttons (page change), aur Booking Date + Vehicle Type slicers hain jo saare pages pe synced hain.

## Part A2 — Extract se Streamlit tak (step by step)

Is part ke end tak cleaning, notebook, SQL aur Streamlit app tere laptop pe chal rahe honge. Total time: ~20 minute.

### Step 1 — Zip extract kar

1. `ola-ride-insights.zip` pe right-click → **Extract All…**
2. Location: `C:\Users\ssa-h\Downloads\` (ya koi bhi folder jiske path mein space na ho).
3. Extract ke baad ye folder hona chahiye: `C:\Users\ssa-h\Downloads\ola-ride-insights\` aur uske andar seedha `app`, `data`, `powerbi`… folders. Agar `ola-ride-insights\ola-ride-insights\` (double folder) ban gaya, to andar wala folder bahar le aa.

### Step 2 — VS Code mein khol

1. VS Code → **File → Open Folder** → `ola-ride-insights` folder chun.
2. **Terminal → New Terminal**. Neeche PowerShell khulega, prompt aisa dikhna chahiye:

```
PS C:\Users\ssa-h\Downloads\ola-ride-insights>
```

Aage ki saari commands isi terminal mein chalani hain.

### Step 3 — Packages install kar

```
python -m pip install -r requirements.txt
python -m pip install ipykernel
```

`ipykernel` notebook chalane ke liye hai. "Requirement already satisfied" aaye to sab pehle se installed hai.

### Step 4 — Data clean kar

```
python src/clean.py
```

Expected output:

```
raw rows: 103,024 -> clean rows: 103,024
written: C:\Users\ssa-h\Downloads\ola-ride-insights\data\processed
```

Isse `data\processed\` mein `ola_rides_clean.csv`, `vehicle_types.csv` aur `ola.db` ban jaate hain. Power BI aur Streamlit dono inhi files se chalte hain.

### Step 5 — EDA notebook chala

1. VS Code mein `notebooks\Ola_Ride_Insights_EDA.ipynb` khol.
2. Upar right mein **Select Kernel → Python Environments →** wahi Python jo terminal mein hai (3.14).
3. Upar **Restart** dabake **Run All**. 1–2 minute lagenge.
4. Check: saare cells ke neeche output aaye, koi red error na ho, 15 charts + missing-values chart dikhe.
5. Notebook ke "GitHub Link" cell mein abhi `https://github.com/<your-username>/ola-ride-insights` likha hai — Step 8 ke baad apna link daal ke save kar.

### Step 6 — Streamlit app chala

```
python -m streamlit run app/app.py
```

(`streamlit run …` seedha nahi chalega, kyunki Scripts folder PATH mein nahi hai — `python -m` wala tareeka hamesha chalega.)

Pehli baar email maange to bas **Enter** daba. Browser mein `http://localhost:8501` khulega. Band karne ke liye terminal mein **Ctrl + C**.

**Har page pe ye check kar:**

- [ ] **Dashboard → Overall:** Total Bookings 103,024 · Successful Rides 63,967 · Success Rate 62.1% · Revenue ₹3.51 Cr · Unique Customers 94,544
- [ ] **Vehicle Type, Revenue, Cancellation, Ratings** tabs pe charts aa rahe hain
- [ ] Sidebar mein Vehicle type = Auto chun → sab numbers badal jaayein → wapas hata de
- [ ] **SQL Query Explorer:** Q1 se Q10 aur X1 se X10 sab result de rahe hain (Q3 = 10,499 · Q5 = 6,542 · Q9 = 3,50,80,467)
- [ ] **Custom SQL** tab mein default query → **Run query** → table aaye
- [ ] **Insights** page khul raha hai
- [ ] **Power BI Report** page abhi khaali message dikhayega — ye normal hai, Part B ke baad bharega

### Step 7 — SQL (MySQL mein chalana ho to, optional)

Streamlit SQLite pe chalta hai, MySQL ki zaroorat nahi. Mentor ko MySQL Workbench mein dikhana ho to:

1. MySQL Workbench khol, apne local server se connect kar.
2. `sql\01_schema_mysql.sql` khol. `LOAD DATA` wali line mein path badal: `C:/Users/ssa-h/Downloads/ola-ride-insights/data/processed/ola_rides_clean.csv` (forward slash `/` use kar).
3. Error 1290/3948 aaye to pehle `SET GLOBAL local_infile = 1;` chala, aur connection settings → **Advanced → Others** mein `OPT_LOCAL_INFILE=1` daal ke reconnect kar.
4. Poori file chala (⚡ icon). End mein `rows_loaded = 103024` aana chahiye.
5. Phir `sql\02_ola_queries.sql` khol aur har query ek-ek karke chala (cursor query pe rakh ke **Ctrl + Enter**).

### Step 8 — GitHub pe push kar

1. github.com → **New repository** → naam `ola-ride-insights` → **Public** → README/gitignore add **mat** kar → Create.
2. Terminal mein:

```
git remote add origin https://github.com/<tera-username>/ola-ride-insights.git
git push -u origin main
```

3. Login popup aaye to GitHub se sign in kar. Push hone ke baad GitHub page refresh kar, saare folders + README dikhne chahiye.
4. Notebook mein GitHub link daal ke, ye chala:

```
git add -A
git commit -m "Add GitHub link"
git push
```

### Step 9 — Streamlit Cloud pe deploy (live link)

1. share.streamlit.io pe **Continue with GitHub** se login kar.
2. **Create app → Deploy a public app from GitHub**.
3. Repository: `<tera-username>/ola-ride-insights` · Branch: `main` · Main file path: `app/app.py`.
4. **Advanced settings → Python version: 3.12** → **Deploy**.
5. 3–5 minute baad app live hogi (pehli baar database banne mein thoda time lagta hai). Ye URL copy karke README mein daal de.

### Troubleshooting

| Problem | Fix |
| --- | --- |
| `streamlit` is not recognized | `python -m streamlit run app/app.py` use kar |
| `python` is not recognized | `py` try kar (`py src/clean.py`), ya Python install karte time "Add to PATH" tick kar |
| `FileNotFoundError ... OLA_DataSet.xlsx` | Galat folder mein ho — terminal ka path `...\ola-ride-insights>` hona chahiye |
| Notebook: "ipykernel required" | `python -m pip install ipykernel` phir kernel dobara select kar |
| Port 8501 busy | `python -m streamlit run app/app.py --server.port 8502` |
| Vehicle icons nahi dikh rahe | Ye internet se load hote hain — net check kar |
| `git push` rejected | GitHub repo banate time README add kar diya tha — `git pull origin main --allow-unrelated-histories` phir `git push` |

## Part B — Power BI (installation se Streamlit embed tak)

Power BI report poori bani hui hai — tujhe sirf data ka path set karna hai, check karna hai, `.pbix` save karna hai aur publish karna hai. Part A ka Step 4 (`python src/clean.py`) pehle ho chuka hona chahiye.

### Step 1 — Power BI Desktop install kar

1. Windows **Start → Microsoft Store** khol → search **Power BI Desktop** → **Get / Install**. (Store se lene pe auto-update hota rehta hai.)
2. Pehle se installed hai to Store → **Library → Get updates** kar le. Purana version `.pbip` files nahi khol paata.
3. Khol ke dekh. Shuru mein sign-in maange to abhi **close/skip** kar sakta hai — sign-in sirf publish (Step 10) ke time chahiye.

### Step 2 — Settings check kar (sirf ek baar)

1. **File → Options and settings → Options → Preview features**.
2. Ye do options dikhen to dono **tick** kar:
    - Power BI Project (.pbip) save option
    - Store reports using enhanced metadata format (PBIR)
3. **OK** → Power BI band karke dobara khol.

Ye options list mein na hon to tension mat le — matlab tere version mein ye already on hain.

### Step 3 — Project khol

1. File Explorer mein `C:\Users\ssa-h\Downloads\ola-ride-insights\powerbi\` pe ja.
2. `OlaRideInsights.pbip` pe **double-click**. (Ya Power BI mein **File → Open → Browse** → neeche file-type dropdown mein *Power BI project files (\*.pbip)* chun → file chun.)
3. Report khulegi — left mein Ola ka green nav panel aur 5 page tabs (Overall, Vehicle Type, Revenue, Cancellation, Ratings) neeche dikhenge.
4. Visuals khaali ya ❌ dikhenge, ya data error aayega — **ye abhi normal hai**, data ka path set nahi hua. Step 4 kar.

### Step 4 — Data ka path set kar (sabse important)

1. **Home** tab → **Transform data** button ke neeche chhota arrow **▼** → **Edit parameters**.
2. **DataFolder** box mein ye daal (end mein `\` zaroori hai):

```
C:\Users\ssa-h\Downloads\ola-ride-insights\data\processed\
```

3. **OK**. Upar peeli patti aaye → **Apply changes**.
4. Popups aa sakte hain:
    - *Privacy levels* → dono files ke liye **Public** chun (ya "Ignore privacy levels" tick) → **Save**
    - *Access a local file / credentials* → **Connect**
5. Neeche "Loading data" chalega, 1–2 minute. Phir **Home → Refresh** ek baar aur daba de.

Aage kabhi project folder ki jagah badle, to sirf yahi Step 4 dobara karna hai.

### Step 5 — Numbers check kar

Power BI cards bade numbers ko K/M mein dikhata hai. Ye values aani chahiye:

| Page | Check kar | Expected |
| --- | --- | --- |
| Overall | Total Bookings · Successful Rides · Success Rate | 103.02K · 63.97K · 62.1% |
| Overall | Revenue (Successful) · Unique Customers | ₹35.08M · 94.54K |
| Vehicle Type | Table mein 7 rows, Auto ka Avg Distance | ~10.04 km (baaki ~25) |
| Revenue | Revenue by Payment Method mein sabse upar | Cash |
| Cancellation | Canceled by Customer · Canceled by Driver · Driver Not Found | 10.5K · 18.43K · 10.12K |
| Ratings | Avg Driver Rating · Avg Customer Rating | 4.00 · 4.00 |

Match ho gaye = report sahi chal rahi hai. Kisi visual pe "Something's wrong" ya ❌ dikhe to us visual ka screenshot mujhe bhej — main fix karke nayi file dunga.

### Step 6 — Navigation aur slicers test kar

1. Desktop mein left ke nav buttons pe **Ctrl + Click** karna padta hai (normal click se sirf select hota hai). Publish ke baad normal click se chalenge.
2. Upar right **Vehicle Type** dropdown mein *Auto* chun → dusre page pe ja → wahan bhi Auto laga hona chahiye (synced). Phir clear kar de.
3. **Booking Date** slider chhota karke dekh, numbers badalne chahiye.

### Step 7 — Apne hisaab se badalna ho to (optional)

Kisi visual pe click → right side **Format** (brush icon) se color, title, font badal sakta hai. Naya visual chahiye to **Visualizations** pane se chun, aur **Data** pane mein `ola_rides` ke andar measures folders mein milenge (1 Volume, 2 Cancellation, 3 Revenue, 4 Distance, 5 Ratings).

### Step 8 — .pbix save kar (submission file)

1. **File → Save as** → **Browse this device**.
2. Folder: `ola-ride-insights\powerbi\` · Save as type: **Power BI file (\*.pbix)** · Name: `OlaRideInsights.pbix` → **Save**.
3. Ye `.pbix` hi submit karni hai. `.pbix` 25 MB se badi ho sakti hai — GitHub pe push karni ho to theek hai (limit 100 MB), warna Drive link de dena.

### Step 9 — Power BI work account bana

Publish ke liye **work/school email** chahiye — Gmail/Outlook personal nahi chalega.

- College ya company ka email hai to wahi use kar.
- Nahi hai to brief ke link **"Steps to Create a Free Power BI Work Account"** wala guide follow kar — usme free work account banane ke steps hain.
- Account banne ke baad app.powerbi.com pe ek baar login karke check kar le.

### Step 10 — Publish kar

1. Power BI Desktop mein upar right **Sign in** → work account se login.
2. `OlaRideInsights.pbix` khula ho → **Home → Publish** → save maange to Save.
3. Destination: **My workspace** → **Select**.
4. "Success!" aayega → **Open 'OlaRideInsights.pbix' in Power BI** pe click. Browser mein report khulegi.
5. Browser mein saare 5 pages check kar le, nav buttons ab normal click se chalne chahiye.

### Step 11 — Publish to web link nikaal

1. app.powerbi.com pe report khuli ho → upar **File** (ya **… / Share** menu) → **Embed report → Publish to web (public)**.
2. **Create embed code** → warning padh ke **Publish**.
3. Do cheezein dikhengi. **"Link you can send in email"** wala link copy kar — aisa dikhega: `https://app.powerbi.com/view?r=eyJrIjoi...`
4. Ye link public hai (koi bhi dekh sakta hai) — data sample hai, isliye problem nahi.

"Publish to web" disabled/grey ho to: app.powerbi.com → ⚙ **Settings → Admin portal → Tenant settings → Export and sharing settings → Publish to web → Enabled → Apply** (agar tu us account ka admin hai). Admin nahi hai to neeche **Plan B** kar.

### Step 12 — Link Streamlit mein daal (local)

**Jaldi test:** `python -m streamlit run app/app.py` → **Power BI Report** page → **Embed settings** box mein link paste → **Enter**. Report wahin dikhne lagegi.

**Permanent (har baar paste na karna pade):**

1. `.streamlit\secrets.toml.example` ko copy kar → same folder mein paste → naam badal ke `secrets.toml` rakh (".example" hata de).
2. File khol, line aisi kar:

```
POWERBI_EMBED_URL = "https://app.powerbi.com/view?r=eyJrIjoi..."
```

3. Save → terminal mein **Ctrl + C** → app dobara chala → **Power BI Report** page pe report apne aap dikhegi.

`secrets.toml` `.gitignore` mein hai, GitHub pe nahi jaayega — jaan-boojh ke.

### Step 13 — Link Streamlit Cloud pe daal (live app)

1. share.streamlit.io → apni app ke aage **⋮ → Settings → Secrets**.
2. Paste kar:

```
POWERBI_EMBED_URL = "https://app.powerbi.com/view?r=eyJrIjoi..."
```

3. **Save** → app reboot hogi → live link pe **Power BI Report** page check kar.

### Plan B — Publish na ho paaye to (screenshots)

Work account ya Publish to web na mile to bhi app mein Power BI dikh jaayega:

1. Power BI Desktop mein har page pe ja → **Win + Shift + S** → sirf report area select kar → Paint mein paste karke PNG save kar.
2. Naam exactly ye rakh aur `assets\powerbi_screens\` folder mein daal: `1_overall.png`, `2_vehicle_type.png`, `3_revenue.png`, `4_cancellation.png`, `5_ratings.png`.
3. App dobara chala → **Power BI Report** page pe link na hone pe ye 5 screenshots tabs mein dikhenge.
4. `git add -A`, `git commit -m "Power BI screenshots"`, `git push` — live app pe bhi aa jaayenge.

### Power BI troubleshooting

| Problem | Fix |
| --- | --- |
| `.pbip` khulta hi nahi / "unsupported" error | Power BI Desktop update kar (Step 1) + Step 2 settings |
| "Could not find file ...ola_rides_clean.csv" | DataFolder path galat / end mein `\` nahi / `clean.py` nahi chalaya |
| Saare visuals khaali | Step 4 ke baad **Home → Refresh** |
| Vehicle table mein icons nahi | Internet on kar (icons flaticon se load hote hain) |
| Nav button click se page nahi badalta | Desktop mein **Ctrl + Click** |
| Publish button grey | Pehle work account se **Sign in** |
| Streamlit pe "refused to connect" | Galat link paste hua — "Link you can send in email" wala `view?r=` link chahiye, iframe code nahi |
| Koi aur error | Screenshot bhej, fix karke nayi file dunga |

## Final submission checklist

20 Nov se pehle ye sab tick ho jaana chahiye:

- [ ] `notebooks\Ola_Ride_Insights_EDA.ipynb` — Run All karke saved, GitHub link bhara hua
- [ ] `sql\02_ola_queries.sql` — 10 brief queries + 10 extra
- [ ] `powerbi\OlaRideInsights.pbix` — Step 8 se saved, numbers Step 5 se match
- [ ] GitHub repo link (public) — README dikh raha ho
- [ ] Streamlit live app link — saare 4 pages chal rahe hon
- [ ] Power BI "Publish to web" link Streamlit mein embedded (ya Plan B screenshots)
- [ ] README mein Streamlit live link add kiya

Kahin bhi atke to us step ka number + screenshot bhej dena.

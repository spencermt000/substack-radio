# Substack Radio - Project Specification

## Project Overview
Build a "radio station" style discovery platform for Substack articles and newsletters. Each day, the platform features different articles and authors across 4 radio "stations" with subcategories. Stations use authentic radio call sign format (e.g., CAPITAL94.1, PULSE95.2). All users see the same content each day based on a deterministic date seed (CST timezone).

### Radio Station Format
- Main stations have call signs like **CAPITAL94**, **PULSE95**, etc.
- Subcategories use decimal notation: **94.1** (main mix), **94.2** (markets), **94.3** (startups)
- The **.1** frequency pulls from ALL subcategories (like a "greatest hits" mix)
- Specific frequencies **.2-.5** show 1-2 articles from that subcategory only

## Station Categories

### 📻 CAPITAL94 - Business, Finance & Innovation
- **94.1** - The Capital Mix (pulls from all subcategories)
- **94.2** - Markets & Investing
- **94.3** - Startups & Tech
- **94.4** - Economics & Business
- **94.5** - Personal Finance & Indie

### 📻 PULSE95 - Media, Culture & Current Events
- **95.1** - The Pulse Mix (pulls from all subcategories)
- **95.2** - News & Current Events
- **95.3** - Pop Culture & Entertainment
- **95.4** - Politics & Society
- **95.5** - Sports & Competition

### 📻 GROWTH96 - Life, Mind & Wellness
- **96.1** - The Growth Mix (pulls from all subcategories)
- **96.2** - Psychology & Self-Help
- **96.3** - Food, Travel & Lifestyle
- **96.4** - Productivity & Learning
- **96.5** - Health & Wellness

### 📻 CREATE97 - Essays, Stories & Ideas
- **97.1** - The Creative Mix (pulls from all subcategories)
- **97.2** - Essays & Commentary
- **97.3** - Fiction & Storytelling
- **97.4** - Philosophy & Big Ideas
- **97.5** - Art & Craft

## Station Configuration (For Code)

```javascript
const STATIONS_CONFIG = {
  CAPITAL94: {
    name: "CAPITAL94",
    displayName: "Business, Finance & Innovation",
    color: "#00B894",
    subcategories: [
      { code: "94.1", name: "The Capital Mix", slug: "main-mix" },
      { code: "94.2", name: "Markets & Investing", slug: "markets" },
      { code: "94.3", name: "Startups & Tech", slug: "startups" },
      { code: "94.4", name: "Economics & Business", slug: "economics" },
      { code: "94.5", name: "Personal Finance & Indie", slug: "finance" }
    ]
  },
  PULSE95: {
    name: "PULSE95",
    displayName: "Media, Culture & Current Events",
    color: "#D63031",
    subcategories: [
      { code: "95.1", name: "The Pulse Mix", slug: "main-mix" },
      { code: "95.2", name: "News & Current Events", slug: "news" },
      { code: "95.3", name: "Pop Culture & Entertainment", slug: "culture" },
      { code: "95.4", name: "Politics & Society", slug: "politics" },
      { code: "95.5", name: "Sports & Competition", slug: "sports" }
    ]
  },
  GROWTH96: {
    name: "GROWTH96",
    displayName: "Life, Mind & Wellness",
    color: "#6C5CE7",
    subcategories: [
      { code: "96.1", name: "The Growth Mix", slug: "main-mix" },
      { code: "96.2", name: "Psychology & Self-Help", slug: "psychology" },
      { code: "96.3", name: "Food, Travel & Lifestyle", slug: "lifestyle" },
      { code: "96.4", name: "Productivity & Learning", slug: "productivity" },
      { code: "96.5", name: "Health & Wellness", slug: "health" }
    ]
  },
  CREATE97: {
    name: "CREATE97",
    displayName: "Essays, Stories & Ideas",
    color: "#00CEC9",
    subcategories: [
      { code: "97.1", name: "The Creative Mix", slug: "main-mix" },
      { code: "97.2", name: "Essays & Commentary", slug: "essays" },
      { code: "97.3", name: "Fiction & Storytelling", slug: "fiction" },
      { code: "97.4", name: "Philosophy & Big Ideas", slug: "philosophy" },
      { code: "97.5", name: "Art & Craft", slug: "craft" }
    ]
  }
};
```

## Tech Stack
- **Frontend**: React (single HTML file with CDN imports for zero hosting cost)
- **Styling**: Tailwind CSS
- **Backend**: Airtable (free tier)
- **Storage**: Claude's persistent storage API for click tracking and daily archives
- **Hosting**: Can be hosted on Vercel/Netlify/GitHub Pages (all free)

## Airtable Schema

### Table 1: Articles
| Field Name | Type | Description |
|------------|------|-------------|
| id | Auto-number | Unique ID |
| title | Single line text | Article title |
| author | Single line text | Author name |
| url | URL | Link to article |
| station_main | Single select | Main station: CAPITAL94, PULSE95, GROWTH96, CREATE97 |
| subcategory | Single select | Subcategory within station (see station definitions above) |
| station_code | Formula | Auto-generates full code like "93.2" or "94.1" |
| submitted_date | Date | When it was submitted |
| approved | Checkbox | Moderation flag (default: unchecked) |
| eligible_date | Formula | submitted_date + 1 day (24hr delay) |
| description | Long text | Brief description/excerpt |
| image_url | URL | Optional thumbnail |

**Formula for `station_code`:**
```
CONCATENATE(
  RIGHT({station_main}, 2),
  SWITCH(
    {subcategory},
    "The Capital Mix", ".1",
    "The Pulse Mix", ".1",
    "The Growth Mix", ".1",
    "The Creative Mix", ".1",
    "Markets & Investing", ".2",
    "Startups & Tech", ".3",
    "Economics & Business", ".4",
    "Personal Finance & Indie", ".5",
    "News & Current Events", ".2",
    "Pop Culture & Entertainment", ".3",
    "Politics & Society", ".4",
    "Sports & Competition", ".5",
    "Psychology & Self-Help", ".2",
    "Food, Travel & Lifestyle", ".3",
    "Productivity & Learning", ".4",
    "Health & Wellness", ".5",
    "Essays & Commentary", ".2",
    "Fiction & Storytelling", ".3",
    "Philosophy & Big Ideas", ".4",
    "Art & Craft", ".5",
    ".1"
  )
)
```

### Table 2: Newsletters
| Field Name | Type | Description |
|------------|------|-------------|
| id | Auto-number | Unique ID |
| name | Single line text | Newsletter/Author name |
| author | Single line text | Author name |
| url | URL | Substack URL |
| station_main | Single select | Primary station: CAPITAL94, PULSE95, GROWTH96, CREATE97 |
| bio | Long text | Short bio |
| submitted_date | Date | When submitted |
| approved | Checkbox | Moderation flag |
| eligible_date | Formula | submitted_date + 1 day |
| image_url | URL | Author photo/logo |

**Note:** Newsletters are associated with main stations only, not subcategories. They appear on the .1 (main mix) frequency.

## Pages Required

### 1. Home Page (`/`)
**Components:**
- Header with logo "SUBSTACK RADIO" and navigation
- 4 station cards, each showing:
  - Station call sign (e.g., "CAPITAL94")
  - Station tagline (e.g., "Business, Finance & Innovation")
  - Featured article of the day from .1 (main mix)
  - Featured newsletter/author of the day
  - "Tune In to 94.1" button linking to station page
- Footer with "Submit" link

### 2. Main Station Page (`/station/{station-code}`)
**Example: `/station/93.1` or `/station/money93`**

**Components:**
- Station header (call sign, full name, vintage radio dial graphic)
- **For .1 (Main Mix) pages:**
  - Featured article (large card with image)
  - Featured newsletter (author spotlight)
  - "Also Playing Today" section showing 1-2 articles from each subcategory (.2, .3, .4, .5)
  - Links to tune into specific frequencies
- **For .2-.5 (Subcategory) pages:**
  - Subcategory name and description
  - 2-3 featured articles from that specific subcategory
  - "Back to [Station].1" button
- Click tracking on all article/newsletter links

**Dial Interface:**
Visual radio dial showing all frequencies:
```
┌──────────────────────────┐
│   CAPITAL94 DIAL         │
│  ○ 94.1 The Capital Mix  │
│  ○ 94.2 Markets          │
│  ○ 94.3 Startups         │
│  ○ 94.4 Economics        │
│  ○ 94.5 Finance & Indie  │
└──────────────────────────┘
```

### 3. Featured Artists Page (`/artists`)
**Components:**
- Header: "Featured Artists / Newsletters"
- 4 sections (one per station)
- Each section shows 2-3 featured newsletters/authors
- Rotates based on same date seed
- Organized by main station (not subcategories)

### 4. Submit Page (`/submit`)
**Components:**
- Two-tab form:
  - Tab 1: Submit Article
  - Tab 2: Submit Newsletter/Author
- **Form fields for Article:**
  - Title, Author, URL, Station (dropdown of 4), Subcategory (dropdown based on station), Description, Image URL (optional)
- **Form fields for Newsletter:**
  - Name, Author, URL, Station (dropdown of 4), Bio, Image URL (optional)
- Submit button that writes to Airtable
- Success message: "Thanks! Your submission will be reviewed and eligible in 24 hours."

### 5. Browse All Frequencies Page (`/browse`) - Optional
**Components:**
- Grid view of all 20 frequencies (4 stations × 5 frequencies)
- Each frequency shows current featured article
- Click any frequency to jump to that page

## Core Features

### 1. Date Seed Logic
```javascript
// Get current CST date (timezone: America/Chicago)
const getCSTDate = () => {
  const now = new Date();
  const cstDate = new Date(now.toLocaleString("en-US", { timeZone: "America/Chicago" }));
  return cstDate.toISOString().split('T')[0]; // YYYY-MM-DD
};

// Deterministic selection based on date + station code
const selectFeatured = (items, date, stationCode, index = 0) => {
  const seed = `${date}-${stationCode}-${index}`;
  const hash = simpleHash(seed);
  return items[hash % items.length];
};

// Simple hash function
const simpleHash = (str) => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
};

// Get featured content for a station frequency
const getFeaturedForFrequency = (allArticles, date, stationMain, subcategory = null) => {
  // If subcategory is null or "Main Mix", pull from ALL subcategories under that station
  let eligibleArticles;
  
  if (!subcategory || subcategory === "Main Mix") {
    // .1 frequency - pull from all subcategories
    eligibleArticles = allArticles.filter(a => a.station_main === stationMain);
  } else {
    // .2-.5 frequency - pull from specific subcategory only
    eligibleArticles = allArticles.filter(a => 
      a.station_main === stationMain && a.subcategory === subcategory
    );
  }
  
  if (eligibleArticles.length === 0) return null;
  
  // Use station code for seed (e.g., "93.1" or "93.2")
  const stationCode = `${stationMain.slice(-2)}.${subcategory ? getSubcategoryNumber(subcategory) : '1'}`;
  return selectFeatured(eligibleArticles, date, stationCode);
};

// Map subcategory to decimal number
const getSubcategoryNumber = (subcategory) => {
  const mapping = {
    // Main mixes (all .1)
    "The Capital Mix": "1",
    "The Pulse Mix": "1",
    "The Growth Mix": "1",
    "The Creative Mix": "1",
    // CAPITAL94
    "Markets & Investing": "2",
    "Startups & Tech": "3",
    "Economics & Business": "4",
    "Personal Finance & Indie": "5",
    // PULSE95
    "News & Current Events": "2",
    "Pop Culture & Entertainment": "3",
    "Politics & Society": "4",
    "Sports & Competition": "5",
    // GROWTH96
    "Psychology & Self-Help": "2",
    "Food, Travel & Lifestyle": "3",
    "Productivity & Learning": "4",
    "Health & Wellness": "5",
    // CREATE97
    "Essays & Commentary": "2",
    "Fiction & Storytelling": "3",
    "Philosophy & Big Ideas": "4",
    "Art & Craft": "5"
  };
  return mapping[subcategory] || "1";
};
```

### 2. Archive Storage
Use Claude's persistent storage to archive daily features:
```javascript
// Store today's featured content
const archiveKey = `archive:${date}`;
await window.storage.set(archiveKey, JSON.stringify({
  date: date,
  stations: {
    'capital94': {
      mainMix: { article: {...}, newsletter: {...} },
      subcategories: {
        'markets': { articles: [...] },
        'startups': { articles: [...] },
        'economics': { articles: [...] },
        'finance': { articles: [...] }
      }
    },
    'pulse95': { mainMix: {...}, subcategories: {...} },
    'growth96': { mainMix: {...}, subcategories: {...} },
    'create97': { mainMix: {...}, subcategories: {...} }
  }
}));
```

### 3. Click Tracking
Track clicks for weekly top articles:
```javascript
// On article click
const trackClick = async (articleId, date) => {
  const clickKey = `clicks:${articleId}`;
  try {
    const result = await window.storage.get(clickKey);
    const clicks = result ? JSON.parse(result.value) : [];
    clicks.push({ date, timestamp: Date.now() });
    await window.storage.set(clickKey, JSON.stringify(clicks));
  } catch (error) {
    console.error('Click tracking failed:', error);
  }
};
```

### 4. Airtable Integration
```javascript
// Airtable config (user needs to provide)
const AIRTABLE_CONFIG = {
  apiKey: 'YOUR_API_KEY',
  baseId: 'YOUR_BASE_ID',
  articlesTable: 'Articles',
  newslettersTable: 'Newsletters'
};

// Fetch approved articles eligible for today
const fetchArticles = async (stationMain, subcategory = null) => {
  const today = getCSTDate();
  const url = `https://api.airtable.com/v0/${AIRTABLE_CONFIG.baseId}/${AIRTABLE_CONFIG.articlesTable}`;
  
  let filterFormula;
  if (subcategory && subcategory !== "Main Mix") {
    // Fetch specific subcategory
    filterFormula = `AND(
      {station_main} = '${stationMain}',
      {subcategory} = '${subcategory}',
      {approved} = TRUE(),
      IS_BEFORE({eligible_date}, DATEADD(TODAY(), 1, 'days'))
    )`;
  } else {
    // Fetch all articles for station (for .1 main mix)
    filterFormula = `AND(
      {station_main} = '${stationMain}',
      {approved} = TRUE(),
      IS_BEFORE({eligible_date}, DATEADD(TODAY(), 1, 'days'))
    )`;
  }
  
  const params = new URLSearchParams({
    filterByFormula: filterFormula
  });
  
  const response = await fetch(`${url}?${params}`, {
    headers: {
      'Authorization': `Bearer ${AIRTABLE_CONFIG.apiKey}`
    }
  });
  
  const data = await response.json();
  return data.records;
};

// Fetch newsletters for a station
const fetchNewsletters = async (stationMain) => {
  const today = getCSTDate();
  const url = `https://api.airtable.com/v0/${AIRTABLE_CONFIG.baseId}/${AIRTABLE_CONFIG.newslettersTable}`;
  
  const params = new URLSearchParams({
    filterByFormula: `AND(
      {station_main} = '${stationMain}',
      {approved} = TRUE(),
      IS_BEFORE({eligible_date}, DATEADD(TODAY(), 1, 'days'))
    )`
  });
  
  const response = await fetch(`${url}?${params}`, {
    headers: {
      'Authorization': `Bearer ${AIRTABLE_CONFIG.apiKey}`
    }
  });
  
  const data = await response.json();
  return data.records;
};

// Submit new article
const submitArticle = async (formData) => {
  const url = `https://api.airtable.com/v0/${AIRTABLE_CONFIG.baseId}/${AIRTABLE_CONFIG.articlesTable}`;
  
  await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${AIRTABLE_CONFIG.apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      fields: {
        title: formData.title,
        author: formData.author,
        url: formData.url,
        station_main: formData.station_main,
        subcategory: formData.subcategory,
        description: formData.description,
        submitted_date: new Date().toISOString().split('T')[0],
        approved: false,
        image_url: formData.image_url || ''
      }
    })
  });
};

// Submit new newsletter
const submitNewsletter = async (formData) => {
  const url = `https://api.airtable.com/v0/${AIRTABLE_CONFIG.baseId}/${AIRTABLE_CONFIG.newslettersTable}`;
  
  await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${AIRTABLE_CONFIG.apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      fields: {
        name: formData.name,
        author: formData.author,
        url: formData.url,
        station_main: formData.station_main,
        bio: formData.bio,
        submitted_date: new Date().toISOString().split('T')[0],
        approved: false,
        image_url: formData.image_url || ''
      }
    })
  });
};
```

### 5. 24-Hour Delay Logic
- Airtable formula field `eligible_date = DATEADD({submitted_date}, 1, 'days')`
- Filter query only fetches records where `eligible_date < TODAY + 1`
- Ensures 24hr buffer for moderation

## How the Subcategory System Works

### Content Flow & Selection
1. **Home Page**: Shows featured content from each of the 4 stations' .1 (main mix) frequency
   - Article: Randomly selected from ALL subcategories under that station
   - Newsletter: Randomly selected from newsletters tagged with that station

2. **Station .1 (Main Mix) Page**:
   - Featured article from ANY subcategory (primary hero)
   - Featured newsletter (secondary hero)
   - "Also Playing Today" section showing 1-2 articles from each .2-.5 subcategory
   - Dial showing all available frequencies

3. **Station .2-.5 (Subcategory) Page**:
   - 2-3 articles ONLY from that specific subcategory
   - No newsletter (newsletters are station-level only)
   - "Back to [Station].1" navigation

### Example User Journey
```
User lands on homepage
  → Sees CAPITAL94.1 featured article about "The Fed's Next Move"
  → Clicks "Tune In to 94.1"
  → Sees CAPITAL94.1 page with:
     - Hero article: "The Fed's Next Move" (from Markets subcategory)
     - Newsletter: "The Macro Compass" by Alfonso Peccatiello
     - Also playing:
       • 94.2: "Tech Stocks Face Reckoning" (Markets)
       • 94.3: "The AI Startup Boom" (Startups)
       • 94.4: "Why Inflation Isn't Dead" (Economics)
       • 94.5: "Building Your Emergency Fund" (Finance & Indie)
  → User clicks "Tune to 94.2" to see more Markets content
  → Sees 94.2 page with 2-3 Markets-only articles
```

### Data Structure Example
```javascript
const todaysFeatured = {
  CAPITAL94: {
    "94.1": {
      article: {
        title: "The Fed's Next Move",
        subcategory: "Markets & Investing",
        // ... pulled from ALL CAPITAL94 articles
      },
      newsletter: {
        name: "The Macro Compass",
        // ... pulled from CAPITAL94 newsletters
      }
    },
    "94.2": [
      { title: "Tech Stocks Face Reckoning", subcategory: "Markets & Investing" },
      { title: "Value Investing in 2025", subcategory: "Markets & Investing" }
    ],
    "94.3": [
      { title: "The AI Startup Boom", subcategory: "Startups & Tech" }
    ],
    // ... etc for 94.4, 94.5
  },
  // ... etc for PULSE95, GROWTH96, CREATE97
}
```

## Routing Structure

The app uses hash-based routing for simplicity (no server required):

```javascript
const routes = {
  '#/': HomePage,
  '#/station/:stationCode': StationPage,  // e.g., #/station/93.1 or #/station/money93
  '#/artists': ArtistsPage,
  '#/submit': SubmitPage,
  '#/browse': BrowseAllPage  // optional
};

// Examples:
// #/ → Home page with all 4 stations
// #/station/94.1 → CAPITAL94 main mix page
// #/station/94.2 → CAPITAL94 Markets subcategory page
// #/station/capital94 → Same as 94.1 (alias)
// #/artists → Featured newsletters/authors
// #/submit → Submission form
```

### URL Patterns
- `/` or `#/` → Home
- `#/station/94.1` → CAPITAL94 main mix
- `#/station/94.2` → CAPITAL94 Markets
- `#/station/capital94` → Alias for 94.1
- `#/artists` → Featured artists
- `#/submit` → Submit form

### Station Code Parsing
```javascript
const parseStationCode = (code) => {
  // Handle both "94.1" and "capital94" formats
  if (code.includes('.')) {
    // Format: "94.1"
    const [stationNum, freq] = code.split('.');
    const stationMap = { '94': 'CAPITAL94', '95': 'PULSE95', '96': 'GROWTH96', '97': 'CREATE97' };
    return { station: stationMap[stationNum], frequency: freq };
  } else {
    // Format: "capital94" → default to .1
    return { station: code.toUpperCase(), frequency: '1' };
  }
};
```

## Implementation Steps

### Step 1: Set up Airtable
1. Create new Airtable base called "Substack Radio"
2. Create "Articles" table with specified schema
3. Create "Newsletters" table with specified schema
4. Add formula for `eligible_date` field: `DATEADD({submitted_date}, 1, 'days')`
5. Generate API key from Airtable account settings
6. Get Base ID from API documentation

### Step 2: Seed Initial Data
Manually add articles and newsletters to Airtable:

**Articles:** Add 20-30 articles total
- Distribute across all 4 stations
- Include 2-4 articles per subcategory (so each station has 8-20 articles)
- Set `approved = true`
- Set `submitted_date` to yesterday or earlier
- Include real Substack URLs where possible

**Example article distribution:**
- CAPITAL94: 3-4 articles each for Markets, Startups, Economics, Finance & Indie
- PULSE95: 3-4 articles each for News, Pop Culture, Politics, Sports
- GROWTH96: 3-4 articles each for Psychology, Lifestyle, Productivity, Health
- CREATE97: 3-4 articles each for Essays, Fiction, Philosophy, Art & Craft

**Newsletters:** Add 10-15 newsletters total
- 2-4 newsletters per station
- Set `approved = true`
- Set `submitted_date` to yesterday or earlier
- Include actual Substack newsletter URLs and bios

This ensures each .1 (main mix) has enough content to pull from, and each .2-.5 frequency has at least 2-3 articles to rotate through.

### Step 3: Build React Component Structure
```
src/
  components/
    Header.jsx
    StationCard.jsx
    ArticleCard.jsx
    NewsletterCard.jsx
    SubmitForm.jsx
  pages/
    Home.jsx
    Station.jsx
    Artists.jsx
    Submit.jsx
  utils/
    airtable.js
    dateUtils.js
    storage.js
  App.jsx
```

### Step 4: Implement Core Features
1. Date seed deterministic selection
2. Airtable fetch functions
3. Storage-based click tracking
4. Daily archive system
5. Submit form with validation

### Step 5: Styling & UX
- Radio-themed design (vintage radio aesthetics?)
- Station-specific color schemes
- Smooth transitions between pages
- Mobile-responsive layout
- Loading states

### Step 6: Testing
- Test date seed produces same results for same day
- Test 24hr delay works correctly
- Test click tracking persists
- Test form submissions write to Airtable
- Test across multiple browsers (storage is browser-specific)

## Design Guidelines

### Color Scheme by Station
- **CAPITAL94**: Green/Currency theme (#00B894, #00D084)
- **PULSE95**: Red/Energy theme (#D63031, #FF7675)
- **GROWTH96**: Purple/Cosmic theme (#6C5CE7, #A29BFE)
- **CREATE97**: Teal/Artistic theme (#00CEC9, #81ECEC)

### Typography
- Headlines: Bold, radio-inspired font (consider: Space Grotesk, Inter Bold, Work Sans Bold)
- Body: Clean, readable sans-serif (Inter, System UI)
- Station call signs: Monospace or bold sans (like radio station IDs)
- Frequency numbers: Tabular/monospace digits for dial aesthetic

### Visual Elements
- Vintage radio dial aesthetic
- Frequency wave visualizations (different per station)
- Analog tuner graphics
- Station "on air" indicators
- Retro LED/VFD display for frequencies
- Static/noise effects on transitions (subtle)
- FM dial markers and indicators

### Radio Dial Component Design
```
┌────────────────────────────────────┐
│          CAPITAL94                  │
│   ●━━━━━○━━━━━━━━━━━━━━━           │
│  94.1  94.2  94.3  94.4  94.5      │
│  MIX   MRKT  START ECON  FIN       │
└────────────────────────────────────┘
```

### Station Card Layout
Each station card on home page should have:
- Call sign in large monospace (e.g., "CAPITAL94")
- Current frequency indicator (e.g., "Now playing: 94.1")
- Featured article thumbnail and title
- Featured newsletter avatar and name
- Vintage radio aesthetic border/frame

## Future Enhancements (V2)
- Weekly "Top Hits" page using click data
- User accounts & preferences
- Playlist feature (save articles for later)
- Email digest of daily features
- RSS feed per station
- Admin dashboard for approvals
- Mobile app
- Social sharing features

## Environment Variables Needed
```env
AIRTABLE_API_KEY=your_api_key_here
AIRTABLE_BASE_ID=your_base_id_here
```
-- *** FOUND IN .env file***

## Deployment
1. Build as single HTML file with inline React
2. Upload to GitHub Pages / Vercel / Netlify
3. Set environment variables in hosting platform
4. Done! Zero ongoing cost.

---

## Quick Start for Claude Code

### Phase 1: Setup & Basic Structure
1. Create Airtable base with Articles and Newsletters tables
2. Add initial seed data (20-30 articles, 10-15 newsletters)
3. Get API credentials (.env file with API key and Base ID)
4. Create single-file React artifact with:
   - Hash-based routing
   - Airtable integration utilities
   - Date seed logic with CST timezone
   - Station configuration (4 stations with subcategories)

### Phase 2: Core Pages
5. Build Home page:
   - 4 station cards showing .1 (main mix) content
   - Featured article + newsletter per station
   - Vintage radio aesthetic
6. Build Station pages:
   - .1 pages: Hero content + "Also Playing" grid
   - .2-.5 pages: Subcategory-specific content
   - Radio dial navigation component
7. Build Artists page:
   - 4 sections for featured newsletters
   - 2-4 per station, date-seeded rotation

### Phase 3: Interactivity
8. Implement storage features:
   - Daily archive system
   - Click tracking
9. Build Submit page:
   - Two-tab form (Articles / Newsletters)
   - Airtable POST integration
   - Form validation

### Phase 4: Polish
10. Add station-specific color theming
11. Create radio dial animations
12. Mobile responsive design
13. Loading states & error handling
14. Test date seed consistency

### File Structure (Single HTML File)
```html
<!DOCTYPE html>
<html>
<head>
  <!-- React, ReactDOM, Tailwind CDN -->
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    // STATIONS_CONFIG constant
    // Airtable utilities
    // Date/seed utilities
    // Storage utilities
    // React components
    // Router
    // App root
  </script>
</body>
</html>
```

The entire app can be built as a single .html file with inline React, making it extremely portable and free to host anywhere.

### Key Implementation Notes
- Use `window.storage` API for click tracking (browser-specific, but acceptable for V1)
- Use deterministic date seed so all users see same content each day
- .1 frequencies pull from ALL subcategories under that station
- .2-.5 frequencies pull ONLY from their specific subcategory
- Newsletters are station-level only (no subcategory association)
- Station codes use last 2 digits (94, 95, 96, 97)
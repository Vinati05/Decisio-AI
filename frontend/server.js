const http = require('http');
const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';

const html = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Nexora Studio</title>
    <style>
      :root {
        color-scheme: light;

        /* Pastel Enterprise Theme (soft, calm, premium) */
        --bg: #FAFAF8; /* main */
        --bg-2: #F6F4F1; /* secondary */
        --surface: #FFFFFF; /* cards */

        --text: #2F3A3D;
        --muted: #6B7280;
        --muted-2: #9CA3AF;

        --border: #E7E5E4;
        --border-2: rgba(231,229,228,0.65);

        --shadow: 0 12px 40px rgba(47,58,61,0.10);
        --shadow-soft: 0 6px 20px rgba(47,58,61,0.08);

        /* Primary accent (soft sage green) */
        --accent: #A8CFA8; /* sage */
        --accent-2: #B7D9B1;
        --accent-3: #8EBF9F;

        /* Secondary accent (dusty blue) */
        --info: #AFCBE8;
        --info-2: #C7DBF3;

        /* Success / Warning / Error */
        --success: #CFE8D5;
        --success-2: #BFE3C5;
        --warning: #F7D8B6;
        --warning-2: #F4C9A5;
        --danger: #F2C2C2;
        --danger-2: #EFB7B7;

        /* Optional purple (AI only) */
        --purple: #DCCCF5;
        --purple-2: #D8C8F0;

        --radius-xl: 16px;
        --radius-lg: 14px;
        --radius-md: 12px;
        --radius-sm: 10px;

        --ring: 0 0 0 3px rgba(142,191,159,0.35);

        --font: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji",
          "Segoe UI Emoji";
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: var(--font);
        background: radial-gradient(900px 500px at 18% 0%, rgba(168,207,168,0.18), transparent 55%),
          radial-gradient(800px 460px at 92% 12%, rgba(175,203,232,0.20), transparent 60%), var(--bg);
        color: var(--text);
        min-height: 100vh;
        padding: 26px;
      }

      a { color: inherit; }

      .app {
        max-width: 1180px;
        margin: 0 auto;
      }

      .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        margin-bottom: 16px;
      }

      .brand {
        display: flex;
        align-items: center;
        gap: 10px;
        user-select: none;
      }

      .logo {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: linear-gradient(180deg, rgba(168,207,168,0.95), rgba(142,191,159,0.55));
        box-shadow: 0 16px 40px rgba(142,191,159,0.22);
        border: 1px solid rgba(47,58,61,0.08);
      }

      .brand h2 {
        margin: 0;
        font-size: 14px;
        font-weight: 750;
        letter-spacing: 0.2px;
      }

      .brand .sub {
        font-size: 12px;
        color: var(--muted);
        margin-top: 2px;
      }

      .pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        background: rgba(255,255,255,0.65);
        border: 1px solid var(--border);
        border-radius: 999px;
        color: var(--muted);
        font-size: 12px;
        white-space: nowrap;
        backdrop-filter: blur(6px);
      }

      .dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: var(--accent-3);
        box-shadow: 0 0 0 3px rgba(142,191,159,0.22);
      }

      .layout {
        background: rgba(255,255,255,0.86);
        border: 1px solid var(--border);
        border-radius: 22px;
        box-shadow: var(--shadow);
        overflow: hidden;
      }

      .header {
        padding: 22px 22px 14px;
        background: linear-gradient(180deg, rgba(255,255,255,0.85), rgba(255,255,255,0.0));
        border-bottom: 1px solid rgba(231,229,228,0.75);
        display: grid;
        grid-template-columns: 1.25fr 0.75fr;
        gap: 18px;
      }

      .header h1 {
        margin: 0;
        font-size: 22px;
        letter-spacing: -0.2px;
      }

      .header p {
        margin: 8px 0 0;
        color: var(--muted);
        line-height: 1.6;
        max-width: 720px;
        font-size: 13px;
      }

      .controls {
        display: flex;
        flex-direction: column;
        gap: 10px;
        align-items: flex-end;
      }

      .btn-row { display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }

      button {
        border: 1px solid var(--border);
        background: rgba(255,255,255,0.72);
        color: var(--text);
        border-radius: 12px;
        padding: 10px 12px;
        font-weight: 680;
        cursor: pointer;
        transition: transform 0.12s ease, background 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
        letter-spacing: 0.1px;
        box-shadow: none;
      }

      button:hover {
        transform: translateY(-1px);
        border-color: var(--border);
        background: rgba(255,255,255,0.88);
        box-shadow: var(--shadow-soft);
      }

      button:focus { outline: none; box-shadow: var(--ring); }

      .primary {
        border-color: rgba(142,191,159,0.55);
        background: linear-gradient(180deg, rgba(168,207,168,0.55), rgba(168,207,168,0.22));
      }

      .primary:hover {
        background: linear-gradient(180deg, rgba(168,207,168,0.65), rgba(168,207,168,0.26));
      }

      .ghost { background: transparent; }

      .grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 14px;
        padding: 16px 16px 18px;
        background: rgba(250,250,248,0.35);
      }

      .story {
        display: grid;
        grid-template-columns: 1.05fr 0.95fr;
        gap: 14px;
        align-items: start;
      }

      .section {
        background: rgba(255,255,255,0.90);
        border: 1px solid rgba(231,229,228,0.9);
        border-radius: var(--radius-xl);
        padding: 16px;
        box-shadow: 0 6px 18px rgba(47,58,61,0.06);
      }

      .section-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 12px;
      }

      .section-title h3 {
        margin: 0;
        font-size: 13px;
        color: #3a484a;
        letter-spacing: 0.2px;
      }

      .section-title .meta {
        color: var(--muted);
        font-size: 12px;
      }

      .stack { display: grid; gap: 12px; }

      .overview {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }

      .metric {
        padding: 14px;
        border-radius: var(--radius-lg);
        background: rgba(255,255,255,0.92);
        border: 1px solid rgba(231,229,228,0.95);
      }

      .metric .label {
        font-size: 12px;
        color: var(--muted);
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .metric .value {
        margin-top: 10px;
        font-size: 22px;
        font-weight: 820;
        letter-spacing: -0.3px;
      }

      .subvalue {
        margin-top: 2px;
        font-size: 12px;
        color: var(--muted);
        line-height: 1.5;
      }

      .confidence-bar {
        height: 10px;
        border-radius: 999px;
        overflow: hidden;
        margin-top: 10px;
        background: rgba(167,170,176,0.10);
        border: 1px solid rgba(231,229,228,0.95);
      }

      .confidence-bar > span {
        display: block;
        height: 100%;
        width: 0%;
        border-radius: 999px;
        background: linear-gradient(90deg, rgba(168,207,168,0.95), rgba(199,219,243,0.95));
        transition: width 0.35s ease;
      }

      .badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }

      .badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 10px;
        border-radius: 999px;
        border: 1px solid rgba(231,229,228,0.95);
        background: rgba(250,250,248,0.70);
        color: var(--muted);
        font-size: 12px;
      }

      .badge .b-dot { width: 8px; height: 8px; border-radius: 999px; }

      .timeline { margin: 8px 0 0; padding: 0; list-style: none; display: grid; gap: 10px; }

      .t-item {
        display: grid;
        grid-template-columns: 16px 1fr;
        gap: 10px;
        align-items: start;
      }

      .t-line {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        margin-top: 4px;
        background: rgba(168,207,168,0.95);
        box-shadow: 0 0 0 3px rgba(142,191,159,0.20);
      }

      .t-body .t-head {
        font-weight: 720;
        font-size: 13px;
        margin: 0;
      }

      .t-body .t-copy {
        margin: 2px 0 0;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.55;
      }

      .evidence-list { display: grid; gap: 10px; }

      details {
        border: 1px solid rgba(231,229,228,0.95);
        background: rgba(255,255,255,0.92);
        border-radius: var(--radius-md);
        padding: 10px 12px;
      }

      summary {
        cursor: pointer;
        list-style: none;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        font-weight: 720;
        font-size: 13px;
      }
      summary::-webkit-details-marker { display: none; }

      .chev {
        width: 10px;
        height: 10px;
        border-right: 2px solid rgba(47,58,61,0.55);
        border-bottom: 2px solid rgba(47,58,61,0.55);
        transform: rotate(45deg);
        transition: transform 0.15s ease;
        margin-left: 8px;
      }

      details[open] .chev { transform: rotate(-135deg); }

      .e-body { margin-top: 10px; }
      .e-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }

      .e-chip {
        padding: 10px 10px;
        border-radius: 12px;
        border: 1px solid rgba(231,229,228,0.95);
        background: rgba(250,250,248,0.78);
      }

      .e-chip .k { font-size: 12px; color: var(--muted); }
      .e-chip .v { margin-top: 4px; font-size: 13px; line-height: 1.4; }

      .approve-card {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
      }

      .status-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }

      .big-title { font-size: 14px; font-weight: 820; margin: 0; }

      .status {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border-radius: 999px;
        border: 1px solid rgba(231,229,228,0.95);
        background: rgba(255,255,255,0.92);
        color: var(--muted);
        font-size: 12px;
      }

      .status .s-dot { width: 8px; height: 8px; border-radius: 999px; background: var(--warning-2); box-shadow: 0 0 0 3px rgba(244,201,165,0.22); }

      .action-buttons { display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-start; }

      .btn-secondary { background: rgba(255,255,255,0.70); }
      .btn-secondary:hover { background: rgba(250,250,248,0.85); }

      .btn-danger { border-color: rgba(242,194,194,0.70); }
      .btn-danger:hover { background: rgba(242,194,194,0.15); }

      .note {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
      }

      .form-row { display: grid; grid-template-columns: 1fr; gap: 8px; }
      textarea {
        width: 100%;
        resize: vertical;
        min-height: 74px;
        padding: 10px 12px;
        border-radius: 12px;
        border: 1px solid rgba(231,229,228,0.95);
        background: rgba(255,255,255,0.92);
        color: var(--text);
        font-family: var(--font);
        font-size: 13px;
        outline: none;
      }

      textarea:focus { box-shadow: var(--ring); border-color: rgba(142,191,159,0.65); }

      .exec {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .exec-list { margin: 0; padding: 0; list-style: none; display: grid; gap: 10px; }

      .exec-item {
        display: grid;
        grid-template-columns: 18px 1fr;
        gap: 10px;
        align-items: start;
      }

      .exec-icon {
        width: 14px;
        height: 14px;
        border-radius: 4px;
        border: 1px solid rgba(231,229,228,0.95);
        background: rgba(255,255,255,0.90);
        margin-top: 3px;
      }
      .exec-icon.ok { background: rgba(191,227,197,0.75); border-color: rgba(142,191,159,0.55); }
      .exec-icon.wait { background: rgba(244,201,165,0.75); border-color: rgba(244,201,165,0.70); }

      .exec-body .h { font-weight: 760; font-size: 13px; margin: 0; }
      .exec-body .c { color: var(--muted); font-size: 12px; line-height: 1.55; margin-top: 2px; }

      @media (max-width: 980px) {
        .header { grid-template-columns: 1fr; }
        .controls { align-items: flex-start; }
        .story { grid-template-columns: 1fr; }
        .overview { grid-template-columns: 1fr; }
        .e-grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="app">
      <div class="topbar">
        <div class="brand">
          <div class="logo" aria-hidden="true"></div>
          <div>
            <h2>Nexora Studio</h2>
            <div class="sub">Explainable Next Best Action platform</div>
          </div>
        </div>
        <div class="pill"><span class="dot"></span><span id="signalPill">Ready</span></div>
      </div>

      <div class="layout">
        <div class="header">
          <div>
            <h1>Design the next step with evidence—not vibes.</h1>
            <p>
              This demo proposes a Next Best Action, shows the supporting enterprise evidence, and leaves a human approval gate
              in place.
            </p>
          </div>
          <div class="controls">
            <div class="btn-row">
              <button class="primary" id="runBtn">Generate recommendation</button>
              <button class="ghost" id="saveBtn">Save to memory</button>
            </div>
            <div class="note" id="memoryBox">No saved decisions yet.</div>
          </div>
        </div>        <div class="grid">
          <div class="story">
            <!-- New Ingestion Center Section -->
            <div style="display: flex; flex-direction: column; gap: 14px; width: 100%;">
              <div class="section">
                <div class="section-title">
                  <h3>Ingestion Center</h3>
                  <div class="meta">Upload text, email, or notes</div>
                </div>
                <div class="upload-container" style="display: flex; flex-direction: column; gap: 10px;">
                  <div style="display: flex; gap: 10px; align-items: center; width: 100%;">
                    <input type="file" id="fileInput" accept=".txt,.json" style="display: none;" />
                    <button type="button" class="btn-secondary" onclick="document.getElementById('fileInput').click()" style="width: 100%; text-align: center; border-style: dashed; border-width: 1px; padding: 12px; font-size: 13px; font-weight: 700; color: var(--muted); cursor: pointer;">
                      📂 Choose Transcript / Email / Notes File
                    </button>
                  </div>
                  <div id="fileInfo" class="note" style="display: none; padding: 10px; background: rgba(0,0,0,0.02); border: 1px solid var(--border); border-radius: var(--radius-md); font-size: 12px; word-break: break-all;"></div>
                  <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 10px;">
                    <div>
                      <label class="note" style="display: block; margin-bottom: 4px; font-weight: 600;">Scenario Domain</label>
                      <select id="domainSelect" style="width:100%; padding: 10px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface); color: var(--text); font-family: var(--font); font-size: 13px;">
                        <option value="saas_sales">SaaS Sales</option>
                        <option value="customer_success">Customer Success</option>
                      </select>
                    </div>
                    <div>
                      <label class="note" style="display: block; margin-bottom: 4px; font-weight: 600;">Customer ID</label>
                      <input type="text" id="customerIdInput" value="CUST-1001" style="width:100%; padding: 9px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--surface); color: var(--text); font-family: var(--font); font-size: 13px;" />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Customer Overview Card -->
              <div class="section">
                <div class="section-title">
                  <h3>Customer overview</h3>
                  <div class="meta" id="customerMeta">—</div>
                </div>

                <div class="overview">
                  <div class="metric">
                    <div class="label">Current health score</div>
                    <div class="value" id="healthValue">—</div>
                    <div class="subvalue" id="healthCopy">—</div>
                  </div>

                  <div class="metric">
                    <div class="label">Recommendation confidence</div>
                    <div class="value" id="signalLabel">—</div>
                    <div class="confidence-bar"><span id="signalBar"></span></div>
                    <div class="subvalue" id="confidenceCopy">—</div>
                  </div>
                </div>

                <div class="badges" id="riskBadges"></div>

                <div style="height:14px"></div>

                <div class="section-title" style="margin-bottom:10px">
                  <h3>Decision timeline</h3>
                  <div class="meta">from interaction → recommendation</div>
                </div>
                <ul class="timeline" id="timeline"></ul>
              </div>
            </div>

            <!-- Next Best Actions List -->
            <div class="section">
              <div class="section-title">
                <h3>Next best actions</h3>
                <div class="meta" id="signalFocusMeta">Explainability • Evidence • Review</div>
              </div>

              <div class="stack" id="actionsList" style="display: flex; flex-direction: column; gap: 14px;">
                <!-- Dynamically populated next best action cards -->
              </div>
            </div>
          </div>

          <div class="story" style="grid-template-columns: 1fr 1fr;">
            <div class="section">
              <div class="section-title">
                <h3>Agent orchestration trace</h3>
                <div class="meta" id="orchestrationRoute">Layer 3 workflow</div>
              </div>
              <ul class="timeline" id="agentTrace"></ul>
            </div>

            <div class="section">
              <div class="section-title">
                <h3>Human approval</h3>
                <div class="meta">review before execution</div>
              </div>

              <div class="approve-card">
                <div class="status-row">
                  <div>
                    <p class="big-title" id="approvalTitle">Recommendation ready</p>
                    <p class="note" style="margin:6px 0 0" id="approvalCopy">Approve to draft outputs, or reject to request more context.</p>
                  </div>
                  <div class="status"><span class="s-dot"></span><span id="approvalStatus">Waiting for review</span></div>
                </div>

                <div class="form-row">
                  <textarea id="reviewerNotes" placeholder="Optional reviewer notes (e.g., constraints, stakeholder concerns)"></textarea>
                </div>

                <div class="action-buttons">
                  <button class="primary" id="approveBtn">Approve</button>
                  <button class="btn-secondary" id="modifyBtn">Modify</button>
                  <button class="btn-secondary btn-danger" id="rejectBtn">Reject</button>
                </div>

                <div class="note" id="approvalResult">—</div>
              </div>
            </div>

            <div class="section">
              <div class="section-title">
                <h3>Execution status</h3>
                <div class="meta">proposed actions</div>
              </div>
              <div class="exec">
                <ul class="exec-list" id="execList"></ul>
                <div class="note">Note: Backend execution is gated. This UI only demonstrates the review layer and explainability.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <script>
      const runBtn = document.getElementById('runBtn');
      const saveBtn = document.getElementById('saveBtn');
      const memoryBox = document.getElementById('memoryBox');

      const signalPill = document.getElementById('signalPill');

      const timeline = document.getElementById('timeline');

      const signalLabel = document.getElementById('signalLabel');
      const signalBar = document.getElementById('signalBar');
      const confidenceCopy = document.getElementById('confidenceCopy');

      const healthValue = document.getElementById('healthValue');
      const healthCopy = document.getElementById('healthCopy');

      const riskBadges = document.getElementById('riskBadges');

      const customerMeta = document.getElementById('customerMeta');
      const signalFocusMeta = document.getElementById('signalFocusMeta');

      const approvalTitle = document.getElementById('approvalTitle');
      const approvalStatus = document.getElementById('approvalStatus');
      const approvalResult = document.getElementById('approvalResult');
      const reviewerNotes = document.getElementById('reviewerNotes');

      const approveBtn = document.getElementById('approveBtn');
      const modifyBtn = document.getElementById('modifyBtn');
      const rejectBtn = document.getElementById('rejectBtn');

      const execList = document.getElementById('execList');
      const agentTrace = document.getElementById('agentTrace');
      const orchestrationRoute = document.getElementById('orchestrationRoute');

      let currentData = null;
      let currentActionState = 'pending'; // pending|approved|rejected|modified
      let uploadedContent = null;
      let uploadedFileName = "";

      // File Input Change Listener
      document.getElementById('fileInput').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;

        uploadedFileName = file.name;
        const reader = new FileReader();
        reader.onload = function(evt) {
          uploadedContent = evt.target.result;

          const fileInfo = document.getElementById('fileInfo');
          fileInfo.style.display = 'block';
          fileInfo.innerHTML = \`<strong>Selected:</strong> \${escapeHtml(file.name)} (\${Math.round(file.size / 1024 * 10) / 10} KB)\`;

          // Auto-detect domain based on file name or content
          const nameLower = file.name.toLowerCase();
          const contentLower = uploadedContent.toLowerCase();
          if (nameLower.includes('customer') || nameLower.includes('success') || nameLower.includes('cs') || contentLower.includes('customer success') || contentLower.includes('ticket') || contentLower.includes('churn')) {
            document.getElementById('domainSelect').value = 'customer_success';
          } else {
            document.getElementById('domainSelect').value = 'saas_sales';
          }
        };
        reader.readAsText(file);
      });

      function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }

      function setSignal(percent) {
        const p = clamp(percent, 0, 100);
        signalLabel.textContent = p + '%';
        signalBar.style.width = p + '%';
      }

      function computeRisk(confidence01) {
        const p = clamp(Math.round(confidence01 * 100), 0, 100);
        if (p >= 82) return { label: 'Low Risk', dot: 'var(--success-2)' };
        if (p >= 70) return { label: 'Medium Risk', dot: 'var(--warning-2)' };
        if (p >= 55) return { label: 'High Risk', dot: 'var(--warning-2)' };
        return { label: 'Blocked', dot: 'var(--danger-2)' };
      }

      function setBadges(confidence01) {
        const risk = computeRisk(confidence01);
        riskBadges.innerHTML = '';

        const conf = Math.round(confidence01 * 100);
        const trust = conf >= 82 ? 'Enterprise-aligned' : conf >= 70 ? 'Partially aligned' : 'Needs more context';

        const badges = [
          { label: risk.label, dot: risk.dot },
          { label: 'Confidence ' + conf + '/100', dot: 'var(--accent-3)' },
          { label: trust, dot: 'var(--accent-3)' },
        ];

        for (const b of badges) {
          const el = document.createElement('div');
          el.className = 'badge';
          el.innerHTML = '<span class="b-dot" style="background:' + b.dot + '; box-shadow: 0 0 0 3px rgba(255,255,255,0.06);"></span><span>' + b.label + '</span>';
          riskBadges.appendChild(el);
        }
      }

      async function loadMemory(customerId) {
        try {
          const response = await fetch(\`/memory/\${customerId}\`);
          const data = await response.json();
          const insights = data.learned_insights || [];
          if (insights.length === 0 || (insights.length === 1 && insights[0].includes("No prior outcomes"))) {
            memoryBox.innerHTML = '<span style="color: var(--muted);">No backend memory records yet. Recommendations are grounded in playbooks.</span>';
          } else {
            memoryBox.innerHTML = '<ul style="margin: 0; padding-left: 16px; display: grid; gap: 6px; text-align: left;">' +
              insights.map(ins => \`<li style="font-size: 12px; color: var(--text); line-height: 1.45;">\${escapeHtml(ins)}</li>\`).join('') +
              '</ul>';
          }
        } catch (e) {
          console.error("Failed to load memory:", e);
          memoryBox.textContent = 'Unable to fetch memory insights.';
        }
      }

      async function updateMemory() {
        const customerId = document.getElementById('customerIdInput') ? document.getElementById('customerIdInput').value.trim() : 'CUST-1001';
        await loadMemory(customerId);
      }

      function renderAgentTrace(data) {
        if (!agentTrace) return;
        agentTrace.innerHTML = '';
        const trace = (data.explanation_bundle && data.explanation_bundle.agent_trace) || [];
        const orch = (data.explanation_bundle && data.explanation_bundle.orchestration) || {};

        if (orchestrationRoute) {
          orchestrationRoute.textContent = orch.route
            ? ('Route: ' + orch.route + ' — ' + (orch.routing_reason || ''))
            : 'Standard workflow';
        }

        if (trace.length === 0) {
          agentTrace.innerHTML = '<li class="t-item"><div class="t-line"></div><div class="t-body"><p class="t-head">No trace yet</p><p class="t-copy">Run a workflow to see agent orchestration.</p></div></li>';
          return;
        }

        trace.forEach(function(entry) {
          const li = document.createElement('li');
          li.className = 't-item';
          const conf = entry.confidence != null ? Math.round(entry.confidence * 100) + '% conf' : '';
          const tools = (entry.tool_usage || []).map(function(t) { return t.tool_name; }).join(', ');
          li.innerHTML = '<div class="t-line"></div><div class="t-body"><p class="t-head">' +
            escapeHtml(entry.agent_name) + ' #' + entry.execution_order + ' (' + entry.duration_ms + 'ms)</p>' +
            '<p class="t-copy">' + escapeHtml(entry.decision) + ': ' + escapeHtml(entry.reason) +
            (conf ? ' • ' + conf : '') +
            (tools ? ' • Tools: ' + escapeHtml(tools) : '') + '</p></div>';
          agentTrace.appendChild(li);
        });
      }

      function renderTimeline(data) {
        const opp = (data.analysis && data.analysis.opportunities && data.analysis.opportunities[0]) || 'Gathering discovery signals.';
        const risk = (data.analysis && data.analysis.risks && data.analysis.risks[0]) || 'Checking risk framing.';
        const missing = (data.analysis && data.analysis.missing_information && data.analysis.missing_information[0]) || 'Identifying open constraints.';
        const formatStr = (data.explanation_bundle && data.explanation_bundle.ingestion_enrichment) 
          ? (data.explanation_bundle.ingestion_enrichment.detected_format || 'raw') 
          : 'raw';
        const sentimentStr = (data.explanation_bundle && data.explanation_bundle.ingestion_enrichment) 
          ? (data.explanation_bundle.ingestion_enrichment.sentiment || 'neutral') 
          : 'neutral';

        const items = [
          { head: 'Customer Interaction Ingested', copy: \`Detected format: \${formatStr}. Sentiment: \${sentimentStr}.\` },
          { head: 'Opportunity Analyzed', copy: opp },
          { head: 'Risk & Missing Info Flagged', copy: \`\${risk} (Gaps: \${missing})\` },
          { head: 'Next Best Actions Generated', copy: \`Proposed \${data.next_best_actions ? data.next_best_actions.length : 0} evidence-linked next steps pending review.\` },
        ];

        timeline.innerHTML = '';
        for (const it of items) {
          const li = document.createElement('li');
          li.className = 't-item';
          li.innerHTML = '<div class="t-line"></div><div class="t-body"><p class="t-head">' + it.head + '</p><p class="t-copy">' + it.copy + '</p></div>';
          timeline.appendChild(li);
        }
      }

      function escapeHtml(str) {
        return String(str)
          .replaceAll('&','&amp;')
          .replaceAll('<','&lt;')
          .replaceAll('>','&gt;')
          .replaceAll('"','&quot;')
          .replaceAll("'",'&#039;');
      }

      function renderExec(data) {
        execList.innerHTML = '';

        const proposed = [
          { state: 'wait', title: 'Draft recommendation outputs', copy: 'Email draft + action plan are prepared but not executed until approved.' },
          { state: 'wait', title: 'Schedule stakeholder alignment', copy: 'A follow-up is proposed using the best next question lane.' },
        ];

        const statusMap = {
          approved: ['ok','ok'],
          modified: ['ok','wait'],
          rejected: ['wait','wait'],
          pending: ['wait','wait']
        };

        const states = statusMap[currentActionState] || statusMap.pending;

        for (let i = 0; i < proposed.length; i++) {
          const st = states[i] || 'wait';
          const li = document.createElement('li');
          li.className = 'exec-item';
          li.innerHTML = '<div class="exec-icon ' + st + '"></div><div class="exec-body"><p class="h">' + proposed[i].title + '</p><p class="c">' + escapeHtml(proposed[i].copy) + '</p></div>';
          execList.appendChild(li);
        }
      }

      function setApprovalUI() {
        if (!currentData) return;
        approvalResult.textContent = '';

        if (currentActionState === 'pending') {
          approvalTitle.textContent = 'Recommendation ready';
          approvalStatus.innerHTML = '<span class="s-dot"></span><span>Waiting for review</span>';
          approvalResult.textContent = 'Choose an outcome to simulate the human gate.';
        } else if (currentActionState === 'approved') {
          approvalTitle.textContent = 'Approved for drafting';
          approvalStatus.innerHTML = '<span class="s-dot" style="background: var(--accent-2); box-shadow: 0 0 0 3px rgba(34,197,94,0.18);"></span><span>Ready to execute (draft)</span>';
          approvalResult.textContent = 'Approved. The platform would now proceed to the drafting workflow.';
        } else if (currentActionState === 'modified') {
          approvalTitle.textContent = 'Approved with changes';
          approvalStatus.innerHTML = '<span class="s-dot" style="background: var(--warning); box-shadow: 0 0 0 3px rgba(245,158,11,0.18);"></span><span>Needs re-planning</span>';
          approvalResult.textContent = 'Modify selected. The planner would incorporate your notes.';
        } else if (currentActionState === 'rejected') {
          approvalTitle.textContent = 'Rejected—request more context';
          approvalStatus.innerHTML = '<span class="s-dot" style="background: var(--danger); box-shadow: 0 0 0 3px rgba(239,68,68,0.18);"></span><span>Blocked</span>';
          approvalResult.textContent = 'Rejected. The platform would ask follow-up questions before proposing again.';
        }

        renderExec(currentData);
      }

      async function submitStepFeedback(customerId, domain, actionTitle, status, idx, buttonEl) {
        const statusTextEl = document.getElementById(\`fb-status-\${idx}\`);
        if (statusTextEl) {
          statusTextEl.textContent = 'Saving...';
        }
        
        try {
          const response = await fetch('/workflow/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              customer_id: customerId,
              domain: domain,
              action_title: actionTitle,
              feedback_status: status
            })
          });
          
          const resData = await response.json();
          if (resData.status === 'success') {
            if (statusTextEl) {
              statusTextEl.textContent = 'Feedback saved!';
              statusTextEl.style.color = 'var(--accent-3)';
              statusTextEl.style.fontWeight = 'bold';
            }
            
            // Highlight current button, reset other button in the same card
            const card = buttonEl.closest('.action-card');
            if (card) {
              const approveBtn = card.querySelector('.approve-step-btn');
              const rejectBtn = card.querySelector('.reject-step-btn');
              
              if (status === 'approved') {
                approveBtn.style.background = 'var(--success-2)';
                approveBtn.style.borderColor = 'var(--success)';
                rejectBtn.style.background = 'rgba(255,255,255,0.72)';
                rejectBtn.style.borderColor = 'var(--border)';
              } else {
                rejectBtn.style.background = 'var(--danger)';
                rejectBtn.style.borderColor = 'var(--danger-2)';
                approveBtn.style.background = 'rgba(255,255,255,0.72)';
                approveBtn.style.borderColor = 'var(--border)';
              }
            }
            
            // Reload memory insights to reflect immediately
            await loadMemory(customerId);
          } else {
            if (statusTextEl) statusTextEl.textContent = 'Error saving feedback';
          }
        } catch (err) {
          console.error(err);
          if (statusTextEl) statusTextEl.textContent = 'Connection error';
        }
      }

      function renderRecommendation(data) {
        currentData = data;

        const overallConf = (data.explanation_bundle && data.explanation_bundle.confidence) 
          ? (data.explanation_bundle.confidence.overall || 0.72) 
          : 0.72;

        setSignal(Math.round(overallConf * 100));

        // Find the evidence sources used across all actions to show in the copy
        const sources = [];
        if (Array.isArray(data.next_best_actions)) {
          data.next_best_actions.forEach(a => {
            if (Array.isArray(a.evidence)) {
              a.evidence.forEach(e => {
                if (e.source && e.source !== 'none') {
                  sources.push(e.source.split(':').pop());
                }
              });
            }
          });
        }
        const uniqueSources = [...new Set(sources)];
        confidenceCopy.textContent = uniqueSources.length > 0
          ? ('Grounded in: ' + uniqueSources.join(', '))
          : 'Higher confidence indicates stronger grounding in enterprise knowledge.';

        setBadges(overallConf);

        // Success metrics (domain KPIs)
        const domain = data.domain || 'saas_sales';
        const metrics = data.success_metrics || {};

        if (domain === 'saas_sales' && metrics.win_probability) {
          document.querySelector('.metric:nth-child(1) .label').textContent = 'Win probability';
          healthValue.textContent = metrics.win_probability.current_estimate;
          healthCopy.textContent = metrics.win_probability.estimated_impact;
        } else if (domain === 'customer_success' && metrics.health_score) {
          document.querySelector('.metric:nth-child(1) .label').textContent = 'Current health score';
          healthValue.textContent = metrics.health_score.current_estimate;
          healthCopy.textContent = metrics.health_score.estimated_impact;
        } else {
          document.querySelector('.metric:nth-child(1) .label').textContent = 'Current health score';
          healthValue.textContent = '—';
          healthCopy.textContent = '—';
        }

        customerMeta.textContent = \`Customer: \${data.customer_id || 'CUST-1001'} • Domain: \${data.domain || 'saas_sales'}\`;
        signalFocusMeta.textContent = 'Explainability • Evidence • Review';

        renderTimeline(data);
        renderAgentTrace(data);

        // Dynamically render next best actions cards list
        const actionsList = document.getElementById('actionsList');
        actionsList.innerHTML = '';

        if (Array.isArray(data.next_best_actions) && data.next_best_actions.length > 0) {
          data.next_best_actions.forEach((action, idx) => {
            const card = document.createElement('div');
            card.className = 'action-card';
            card.style = 'border: 1px solid var(--border); padding: 14px; border-radius: var(--radius-md); background: var(--surface); transition: box-shadow 0.15s ease, border-color 0.15s ease; position: relative;';
            
            const confPercent = Math.round(action.confidence * 100);
            
            // Generate evidence items HTML
            const evidenceHTML = action.evidence.map(e => \`
              <div class="e-chip" style="padding: 10px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--bg-2);">
                <div class="k" style="font-size: 11px; font-weight: 700; color: var(--muted);">\${escapeHtml(e.label)}</div>
                <div class="v" style="font-size: 12px; margin-top: 4px; line-height: 1.4;">\${escapeHtml(e.excerpt)}</div>
                <div class="note" style="font-size: 10px; margin-top: 6px; color: var(--muted-2);">Source: \${escapeHtml(e.source)}</div>
              </div>
            \`).join('');
            
            card.innerHTML = \`
              <div style="display: flex; justify-content: space-between; align-items: start; gap: 10px;">
                <div>
                  <span class="note" style="text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px; color: var(--muted); font-weight: 700;">Step \${idx + 1}</span>
                  <h4 style="margin: 4px 0 6px; font-size: 15px; font-weight: 800; color: var(--text);">\${escapeHtml(action.title)}</h4>
                </div>
                <div>
                  <span class="badge" style="background: var(--accent-2); color: var(--text); border-color: rgba(142,191,159,0.3); font-weight: 700; white-space: nowrap;">
                    \${confPercent}% Confidence
                  </span>
                </div>
              </div>
              <p class="note" style="margin: 8px 0 10px; font-size: 13px; line-height: 1.5; color: var(--text);">\${escapeHtml(action.summary)}</p>
              
              <div class="note" style="margin: 8px 0; font-style: italic; border-left: 3px solid var(--accent); padding: 8px 10px; background: rgba(0,0,0,0.02); border-radius: 0 6px 6px 0; font-size: 12px; line-height: 1.4;">
                <strong>Scaffolding Rationale:</strong> \${escapeHtml(action.rationale)}
              </div>

              <details style="margin-top: 10px; border: 1px solid var(--border-2); border-radius: var(--radius-sm); background: rgba(255,255,255,0.5);">
                <summary style="font-size: 12px; font-weight: 700; color: var(--muted); padding: 6px 8px; cursor: pointer; display: flex; align-items: center; justify-content: space-between;">
                  <span>Grounded Enterprise Evidence</span>
                  <span class="chev" style="margin-left: auto;"></span>
                </summary>
                <div class="e-body" style="padding: 8px; display: grid; grid-template-columns: 1fr; gap: 8px; background: var(--bg);">
                  \${evidenceHTML}
                </div>
              </details>

              <div style="display: flex; gap: 8px; margin-top: 14px; justify-content: flex-end; align-items: center; border-top: 1px solid var(--border-2); padding-top: 10px;">
                <span class="note" style="font-size: 11px; color: var(--muted); margin-right: auto;" id="fb-status-\${idx}">Rate this step:</span>
                <button class="btn-secondary approve-step-btn" data-title="\${escapeHtml(action.title)}" data-idx="\${idx}" style="padding: 6px 12px; font-size: 12px; display: inline-flex; align-items: center; gap: 4px; border-radius: 8px;">
                  👍 Approve
                </button>
                <button class="btn-secondary reject-step-btn btn-danger" data-title="\${escapeHtml(action.title)}" data-idx="\${idx}" style="padding: 6px 12px; font-size: 12px; display: inline-flex; align-items: center; gap: 4px; border-radius: 8px;">
                  👎 Reject
                </button>
              </div>
            \`;
            actionsList.appendChild(card);
          });

          // Bind feedback buttons click listeners
          const customerId = document.getElementById('customerIdInput').value.trim() || 'CUST-1001';
          const domain = document.getElementById('domainSelect').value;

          cardContainerListeners(customerId, domain);
        } else {
          actionsList.innerHTML = '<p class="note">No actions proposed for the current context.</p>';
        }

        currentActionState = 'pending';
        reviewerNotes.value = '';
        setApprovalUI();

        signalPill.textContent = 'Recommendation ready';
      }

      function cardContainerListeners(customerId, domain) {
        document.querySelectorAll('.approve-step-btn').forEach(btn => {
          btn.addEventListener('click', async function() {
            const actionTitle = this.getAttribute('data-title');
            const idx = this.getAttribute('data-idx');
            await submitStepFeedback(customerId, domain, actionTitle, 'approved', idx, this);
          });
        });

        document.querySelectorAll('.reject-step-btn').forEach(btn => {
          btn.addEventListener('click', async function() {
            const actionTitle = this.getAttribute('data-title');
            const idx = this.getAttribute('data-idx');
            await submitStepFeedback(customerId, domain, actionTitle, 'rejected', idx, this);
          });
        });
      }

      function setLoading() {
        signalPill.textContent = 'Curating context…';
        signalFocusMeta.textContent = 'Preparing evidence summaries';
        timeline.innerHTML = '';
        const actionsList = document.getElementById('actionsList');
        if (actionsList) {
          actionsList.innerHTML = \`
            <div style="text-align: center; padding: 30px; color: var(--muted);">
              <div style="font-size: 13px; font-weight: 600; margin-bottom: 6px;">Curating Next Best Actions...</div>
              <div class="note">Retrieving playbook patterns and analyzing business context.</div>
            </div>
          \`;
        }
        setSignal(72);
        healthValue.textContent = '—';
        healthCopy.textContent = '—';
        riskBadges.innerHTML = '';
        execList.innerHTML = '';
        if (agentTrace) agentTrace.innerHTML = '';
        if (orchestrationRoute) orchestrationRoute.textContent = 'Curating agents…';

        approvalResult.textContent = '';
        currentActionState = 'pending';
        approvalTitle.textContent = 'Recommendation ready';
        approvalStatus.innerHTML = '<span class="s-dot"></span><span>Waiting for review</span>';
      }

      async function loadRecommendation() {
        setLoading();
        try {
          const customerId = document.getElementById('customerIdInput').value.trim() || 'CUST-1001';
          const domain = document.getElementById('domainSelect').value;

          let payload = {
            customer_id: customerId,
            domain: domain
          };

          if (uploadedContent) {
            if (uploadedFileName.endsWith('.json')) {
              try {
                const parsed = JSON.parse(uploadedContent);
                payload = { ...payload, ...parsed };
              } catch (err) {
                payload.interaction_text = uploadedContent;
              }
            } else {
              payload.interaction_text = uploadedContent;
            }
          } else {
            payload.interaction_text = "VP Ops wants faster reporting (4hr manual). No champion yet. Competitor X mentioned. IT asked about SSO.";
          }

          const response = await fetch('/workflow/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          const data = await response.json();
          renderRecommendation(data);
          await loadMemory(customerId);
        } catch (e) {
          console.error(e);
          signalPill.textContent = 'Connection issue';
          setSignal(48);
          timeline.innerHTML = '';
          const actionsList = document.getElementById('actionsList');
          if (actionsList) {
            actionsList.innerHTML = '<div style="padding: 20px; color: var(--muted); text-align: center;">Backend not reachable. Start the backend container and try again.</div>';
          }
          execList.innerHTML = '';
          currentActionState = 'pending';
          setApprovalUI();
        }
      }

      runBtn.addEventListener('click', function () {
        loadRecommendation();
      });

      saveBtn.addEventListener('click', function () {
        if (!currentData) return;
        localStorage.setItem('nexora-spark', (currentData.next_best_actions && currentData.next_best_actions[0]) ? currentData.next_best_actions[0].title : 'Action');
        updateMemory();
      });

      approveBtn.addEventListener('click', function () {
        currentActionState = 'approved';
        const notes = reviewerNotes.value.trim();
        if (notes) approvalResult.textContent = 'Approved. Notes captured: "' + escapeHtml(notes) + '"';
        else approvalResult.textContent = 'Approved. Notes captured: none.';
        setApprovalUI();
      });

      modifyBtn.addEventListener('click', function () {
        currentActionState = 'modified';
        const notes = reviewerNotes.value.trim();
        approvalResult.textContent = notes ? ('Modify selected. Notes: "' + escapeHtml(notes) + '"') : 'Modify selected. Add notes to refine the planner output.';
        setApprovalUI();
      });

      rejectBtn.addEventListener('click', function () {
        currentActionState = 'rejected';
        const notes = reviewerNotes.value.trim();
        approvalResult.textContent = notes ? ('Rejected. Notes: "' + escapeHtml(notes) + '"') : 'Rejected. Add notes to request more context.';
        setApprovalUI();
      });

      updateMemory();
      setSignal(92);
      // initial empty state
      signalPill.textContent = 'Ready';
      
      const actionsList = document.getElementById('actionsList');
      if (actionsList) {
        actionsList.innerHTML = \`
          <div style="padding: 20px; color: var(--muted); text-align: center;">
            <div style="font-weight: 700; margin-bottom: 6px;">Generate to see the next best actions</div>
            <div class="note">Choose a file, specify scenario options, and run generation.</div>
          </div>
        \`;
      }

      customerMeta.textContent = 'Customer: CUST-1001 • Domain: saas_sales';
      confidenceCopy.textContent = 'Higher confidence indicates stronger grounding in enterprise knowledge.';

      // Default exec placeholders
      currentActionState = 'pending';
      setApprovalUI();

      // Default exec placeholders content
      execList.innerHTML = '';
      renderExec({});

      loadRecommendation();
    </script>
  </body>
</html>`;


function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(payload));
}

const server = http.createServer((req, res) => {
  if (req.url === '/planner/run') {
    const target = backendUrl + '/planner/run';
    http.get(target, (backendRes) => {
      let data = '';
      backendRes.on('data', (chunk) => (data += chunk));
      backendRes.on('end', () => {
        try {
          sendJson(res, backendRes.statusCode || 200, JSON.parse(data));
        } catch {
          sendJson(res, 502, { error: 'Backend error' });
        }
      });
    }).on('error', () => sendJson(res, 502, { error: 'Unable to reach backend' }));
    return;
  }

  if (req.url === '/workflow/start' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      const target = backendUrl + '/workflow/start';
      const parsedUrl = new URL(target);
      const options = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body)
        }
      };
      const backendReq = http.request(options, (backendRes) => {
        let responseData = '';
        backendRes.on('data', (chunk) => (responseData += chunk));
        backendRes.on('end', () => {
          try {
            sendJson(res, backendRes.statusCode || 200, JSON.parse(responseData));
          } catch {
            sendJson(res, 502, { error: 'Backend error' });
          }
        });
      });
      backendReq.on('error', () => sendJson(res, 502, { error: 'Unable to reach backend' }));
      backendReq.write(body);
      backendReq.end();
    });
    return;
  }

  if (req.url === '/workflow/feedback' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      const target = backendUrl + '/workflow/feedback';
      const parsedUrl = new URL(target);
      const options = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body)
        }
      };
      const backendReq = http.request(options, (backendRes) => {
        let responseData = '';
        backendRes.on('data', (chunk) => (responseData += chunk));
        backendRes.on('end', () => {
          try {
            sendJson(res, backendRes.statusCode || 200, JSON.parse(responseData));
          } catch {
            sendJson(res, 502, { error: 'Backend error' });
          }
        });
      });
      backendReq.on('error', () => sendJson(res, 502, { error: 'Unable to reach backend' }));
      backendReq.write(body);
      backendReq.end();
    });
    return;
  }

  if (req.url.startsWith('/memory/') && req.method === 'GET') {
    const target = backendUrl + req.url;
    http.get(target, (backendRes) => {
      let data = '';
      backendRes.on('data', (chunk) => (data += chunk));
      backendRes.on('end', () => {
        try {
          sendJson(res, backendRes.statusCode || 200, JSON.parse(data));
        } catch {
          sendJson(res, 502, { error: 'Backend error' });
        }
      });
    }).on('error', () => sendJson(res, 502, { error: 'Unable to reach backend' }));
    return;
  }

  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
});

server.listen(3000, '0.0.0.0', () => console.log('Frontend listening on port 3000'));

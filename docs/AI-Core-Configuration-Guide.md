# AI Core Configuration Guide

This guide explains how to configure the AI Core central router for
production use. After completing these steps, 7 modules will use AI
for intelligent responses.

## Prerequisites

1. Install `l10n_si_ai_core` module (Apps → Update → Search "AI Core")
2. Have at least one AI provider configured (see Step 1)

## Step 1: Configure AI Concierge Config (Provider Credentials)

The AI Core router uses `l10n_si.ai.concierge.config` records as
provider credentials. You need at least one config per provider.

**Go to:** AI Concierge (SI) → Configuration

Create one config per LLM provider you want to use:

### Option A: Puter.com (FREE — recommended for testing)

| Field | Value |
|-------|-------|
| Name | Puter GLM 5.1 |
| AI Backend | `Puter.com (FREE — GLM 5.1, GPT-4o, Claude)` |
| API Key | Your Puter auth token (from puter.com) |
| Model Name | `z-ai/glm-5.1` |
| Max Tokens | `1000` (GLM 5.1 needs 1000+ for reasoning) |
| Temperature | `0.7` |
| Active | ✅ |

### Option B: Z.AI (production — low latency)

| Field | Value |
|-------|-------|
| Name | ZAI GLM 4 Plus |
| AI Backend | `ZAI (GLM)` |
| API Key | Your Z.AI API key |
| Model Name | `glm-4-plus` |
| Max Tokens | `500` |
| Temperature | `0.7` |
| Active | ✅ |

### Option C: OpenAI (highest quality)

| Field | Value |
|-------|-------|
| Name | OpenAI GPT-4o |
| AI Backend | `OpenAI (GPT-4)` |
| API Key | Your OpenAI API key |
| Model Name | `gpt-4o` |
| Max Tokens | `500` |
| Active | ✅ |

## Step 2: Configure AI Core Providers

**Go to:** Settings → AI Core → Providers

For each AI Concierge config you created in Step 1, create a
corresponding AI Core Provider:

### Provider 1: Puter (multilingual — primary)

| Field | Value |
|-------|-------|
| Config | Puter GLM 5.1 |
| Task Type | `multilingual` |
| Priority | `1` (primary — tried first) |
| Max Tokens Override | `1000` |
| Active | ✅ |

### Provider 2: OpenAI (simple — fast responses)

| Field | Value |
|-------|-------|
| Config | OpenAI GPT-4o |
| Task Type | `simple` |
| Priority | `2` |
| Active | ✅ |

### Provider 3: ZAI (general — fallback)

| Field | Value |
|-------|-------|
| Config | ZAI GLM 4 Plus |
| Task Type | `general` |
| Priority | `5` (last fallback) |
| Active | ✅ |

### Provider 4: Puter (creative — marketing/reviews)

| Field | Value |
|-------|-------|
| Config | Puter GLM 5.1 |
| Task Type | `creative` |
| Priority | `3` |
| Active | ✅ |

### Provider 5: Puter (reasoning — helpdesk/reports/dashboard)

| Field | Value |
|-------|-------|
| Config | Puter GLM 5.1 |
| Task Type | `reasoning` |
| Priority | `3` |
| Active | ✅ |

## Step 3: Configure AI Core Routes (optional)

**Go to:** Settings → AI Core → Routes

Routes define default parameters for each task type. Create one
route per task type:

### Route: multilingual (AI Concierge + WhatsApp)

| Field | Value |
|-------|-------|
| Task Type | `multilingual` |
| System Prompt | `Si prijazen AI asistent v slovenskem hotelu. Odgovarjaj v slovenščini, jedrnato in prijazno.` |
| Temperature | `0.7` |
| Max Tokens | `1000` |

### Route: creative (Marketing + Reviews)

| Field | Value |
|-------|-------|
| Task Type | `creative` |
| System Prompt | `Si izkušen copywriter za hotelirstvo. Pišeš privlačne, osebne e-maile v slovenščini.` |
| Temperature | `0.8` (more creative) |
| Max Tokens | `1000` |

### Route: reasoning (Helpdesk + Reports + Dashboard)

| Field | Value |
|-------|-------|
| Task Type | `reasoning` |
| System Prompt | `Si izkušen analitik. Analiziraš podatke in daješ praktična priporočila, v slovenščini.` |
| Temperature | `0.3` (more deterministic) |
| Max Tokens | `1000` |

## Step 4: Enable AI in Individual Modules

### AI Concierge (automatic)
No action needed — AI Concierge automatically uses AI Core when installed.

### WhatsApp Business (enable auto-reply)
**Go to:** Settings → Companies → [Your Company]
- Set `wa_enabled` = ✅
- Set `wa_auto_reply` = ✅
- Configure WhatsApp credentials (phone_number_id, access_token)

### Marketing Automation
**Go to:** Marketing → Campaigns → [Campaign] → Form
- Click "🤖 Generiraj AI vsebino" button
- AI generates subject + body for all email steps
- Review and save

### Review Management
**Go to:** Reviews → [Review] → Form
- Click "AI predlog odgovora" button
- AI generates personalized response
- Review and click "Pošlji odgovor"

### Helpdesk
**Go to:** Helpdesk → Tickets → [Ticket] → Form
- Click "🤖 AI predlog" button
- AI suggests solution steps
- Review and use as basis for response

### Reports
**Go to:** SI Reports → [Report] → Form
- Click "🤖 AI povzetek" button
- AI generates management summary from XML content

### Executive Dashboard
**Go to:** Dashboard → [Dashboard] → Form
- Click "🤖 AI analiza" button
- AI analyzes KPIs and gives insights + recommendations

## Step 5: Monitor AI Usage

**Go to:** Settings → AI Core → Usage

This shows:
- Total API calls (success + failed)
- Breakdown by provider (Puter, ZAI, OpenAI)
- Breakdown by module (Concierge, WhatsApp, Marketing, etc.)
- Breakdown by task type (multilingual, creative, reasoning)
- Error messages for failed calls

## Fallback Chain (How It Works)

When a module calls `ai.core.generate(task_type='multilingual')`:

```
1. Try Puter GLM 5.1 (priority 1)
   ├─ Success → return response
   └─ Fail (auth/rate-limit/timeout)
       ↓
2. Try ZAI GLM 4+ (priority 5, general fallback)
   ├─ Success → return response
   └─ Fail
       ↓
3. All providers failed → return error
   ↓
4. Module falls back to existing behavior
   (rule-based / templates / canned responses)
```

## Troubleshooting

### "No AI providers configured for task: multilingual"
- Go to Settings → AI Core → Providers
- Create a provider with Task Type = `multilingual`
- Make sure it's Active and has a valid Config

### "Puter auth error (401)"
- Your Puter token may be expired or invalid
- Get a new token from puter.com
- Update the AI Concierge Config's API Key field

### "Puter rate limit exceeded (429)"
- Puter free tier has rate limits
- Add a second provider (ZAI or OpenAI) as fallback
- The router will automatically try the next provider

### "GLM 5.1 returns empty response"
- GLM 5.1 uses 800+ tokens for internal reasoning
- Increase Max Tokens to 1000+ in the config
- Or use GPT-4o (more token-efficient)

### AI button not visible in Odoo
- Make sure `l10n_si_ai_core` is installed
- Upgrade the module (Apps → Update Apps List → Upgrade)
- Check that the view is updated (clear browser cache)

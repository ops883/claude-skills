# Email Template Best Practices

Reference material for deliverability, accessibility, dark mode, and multi-provider setup.

---

## Email Client Compatibility

| Feature | Gmail | Outlook | Apple Mail | Yahoo |
|---------|-------|---------|------------|-------|
| Flexbox | ❌ | ❌ | ✅ | ❌ |
| CSS Grid | ❌ | ❌ | ✅ | ❌ |
| `<style>` in `<head>` | ✅ | ❌ | ✅ | ✅ |
| Inline styles | ✅ | ✅ | ✅ | ✅ |
| Dark mode media query | ✅ | ✅ | ✅ | ❌ |
| Web fonts | ✅ | ❌ | ✅ | ❌ |
| Background images | ✅ | ⚠️ | ✅ | ✅ |
| `border-radius` | ✅ | ❌ | ✅ | ✅ |

**Rule of thumb:** Use table-based layouts for Outlook. React Email handles this automatically.

---

## Deliverability Checklist

### Authentication (DNS)
- [ ] **SPF** record set for your sending domain
- [ ] **DKIM** signing enabled on your ESP (Resend, SendGrid, etc.)
- [ ] **DMARC** policy set to at least `p=none` for monitoring

### Content
- [ ] Subject line < 60 characters (mobile preview)
- [ ] Preview text set (appears next to subject in inbox)
- [ ] Text-to-image ratio > 60:40 (image-heavy emails land in spam)
- [ ] No URL shorteners (bit.ly, t.co trigger spam filters)
- [ ] Unsubscribe link present for marketing emails
- [ ] Physical mailing address in footer (CAN-SPAM / GDPR requirement for marketing)

### Sending
- [ ] Separate sending domains for transactional vs. marketing
- [ ] Warm up new sending domains gradually (start < 100/day)
- [ ] Bounce handling: remove hard bounces immediately
- [ ] Complaint handling: remove users who mark as spam

---

## Dark Mode Support

Email clients that support dark mode will invert or adjust colors. Protect your brand:

```tsx
// Add data-ogsc attributes for Outlook dark mode
// Use @media (prefers-color-scheme: dark) for Apple Mail / Gmail
<Head>
  <style>{`
    @media (prefers-color-scheme: dark) {
      .email-body { background-color: #1a1a1a !important; }
      .email-card { background-color: #2d2d2d !important; }
      .email-text { color: #e5e5e5 !important; }
      .email-muted { color: #9ca3af !important; }
    }
  `}</style>
</Head>
```

**Safe colors for dark mode:**
- Avoid pure black (#000000) backgrounds — use #1a1a1a instead
- Avoid pure white (#ffffff) text — use #f5f5f5 instead
- Test your primary color at different contrast ratios (WCAG AA = 4.5:1)

---

## Accessibility

- **Alt text** on every image (empty alt="" for decorative images)
- **lang** attribute on `<html>` element (screen reader language)
- **role="presentation"** on layout tables
- **Minimum font size** 14px body, 18px headings
- **Sufficient color contrast** — WCAG AA: 4.5:1 for body text
- **Tap target size** — buttons minimum 44×44px on mobile
- **Plain-text version** — all major ESPs require it; users with screen readers often prefer it

---

## Provider Setup

### Resend (recommended for new projects)
```typescript
import { Resend } from "resend";
const resend = new Resend(process.env.RESEND_API_KEY);

await resend.emails.send({
  from: "MyApp <hello@yourdomain.com>",
  to: [user.email],
  subject: "Welcome to MyApp",
  react: <WelcomeEmail userFirstName={user.firstName} />,
});
```

### SendGrid
```typescript
import sgMail from "@sendgrid/mail";
sgMail.setApiKey(process.env.SENDGRID_API_KEY!);
const { html } = await render(<WelcomeEmail userFirstName={user.firstName} />);

await sgMail.send({
  to: user.email,
  from: "hello@yourdomain.com",
  subject: "Welcome to MyApp",
  html,
});
```

### SES (AWS)
```typescript
import { SES } from "@aws-sdk/client-ses";
const ses = new SES({ region: "us-east-1" });
const { html, text } = await render(<WelcomeEmail />, { plainText: true });

await ses.sendEmail({
  Source: "hello@yourdomain.com",
  Destination: { ToAddresses: [user.email] },
  Message: {
    Subject: { Data: "Welcome to MyApp" },
    Body: { Html: { Data: html }, Text: { Data: text } },
  },
});
```

---

## Spam Score Optimization

High-risk patterns that trigger spam filters:

| Pattern | Risk | Fix |
|---------|------|-----|
| ALL CAPS subject | High | Use sentence case |
| Excessive `!!!!` | High | Remove |
| "Free", "Click here", "Act now" | Medium | Rephrase to be specific |
| URL shorteners | High | Use full branded URLs |
| Mismatched From/Reply-To domains | Medium | Align domains |
| < 100 words body text | Medium | Add value content |
| No unsubscribe (marketing) | Very High | Required by law |

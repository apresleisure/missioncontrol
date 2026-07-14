# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
// tools/dynamicShippingEngine.js
module.exports = {
  calculateWorstCaseMargin: (retailPrice, baseCost) => {
    const SHIPPING_BUFFER = 850; // $8.50 worst-case individual softgood shipping
    const BUNDLE_DISCOUNT = 0.75; // 25% off auto-trigger for $150+ carts
    
    const worstCaseRetail = (retailPrice * BUNDLE_DISCOUNT) / 100;
    const baseCostDec = baseCost / 100;
    const shippingDec = SHIPPING_BUFFER / 100;
    
    const netMargin = worstCaseRetail - baseCostDec - shippingDec;
    const marginPercentage = (netMargin / worstCaseRetail) * 100;
    
    return {
      safe: marginPercentage >= 40,
      actualMargin: marginPercentage
    };
  }
};
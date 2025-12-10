# ETPS Open Source Strategy

## Purpose

This document captures the strategic rationale for making ETPS an open source project, along with the path forward if commercialization is desired in the future.

## Current Status: Open Source Portfolio Project

ETPS is published as an **open source portfolio project** under the MIT License. The primary goals are:

1. **Demonstrate AI Engineering Skills** - Full-stack AI application with LLM orchestration, vector search, semantic matching, and quality evaluation loops
2. **Show System Design Capability** - Production deployment with Railway, Vercel, PostgreSQL, and Qdrant Cloud
3. **Provide Working Reference** - Others can learn from or build upon this architecture

## Why Open Source Makes Sense

### The Code is Infrastructure, Not the Moat

The value in AI products comes from:

| Asset | Shareable? | Why It Matters |
|-------|------------|----------------|
| Application code | Yes | Infrastructure - well-documented patterns |
| Prompt engineering | Evolves | The "secret sauce" that improves with iteration |
| User feedback data | Private | What actually works for real users |
| Fine-tuned models | Private | If you train custom models later |
| Brand and trust | Personal | "Benjamin Black's tool" - reputation |
| Execution speed | Personal | Deep understanding enables rapid iteration |

The codebase itself is valuable for learning and demonstration, but **execution and iteration** create the real competitive advantage.

### Benefits of Open Source

1. **Portfolio credibility** - Code is visible, not just claims
2. **Community feedback** - Others may spot issues or improvements
3. **Trust signal** - Transparency demonstrates confidence
4. **Learning resource** - Helps others building similar systems

## What's Included

### Public (In This Repository)
- Complete FastAPI backend with 711+ tests
- Next.js frontend with shadcn/ui
- Claude Code skills demonstrating AI-assisted development
- Deployment guides for Railway, Vercel, Qdrant Cloud
- Documentation of architecture and data models

### Private (Not Included)
- Production API keys and secrets
- User data and generated documents
- Personal resume/experience content (in production database)
- Any future premium features

## Future Commercialization Path

If ETPS is commercialized in the future, the strategy would be:

### 1. Fork to Private Repository
- Create private fork of current state
- Continue public version as "community edition"
- Add proprietary features in private fork

### 2. Potential Premium Features
- Multi-user authentication and team features
- Advanced analytics and insights
- Custom model fine-tuning
- Priority support and SLA
- White-label/enterprise deployment

### 3. Open Core Model
Many successful companies use this approach:
- Free tier: Open source, self-hosted
- Premium tier: Managed hosting, advanced features
- Enterprise: Custom deployment, support contracts

## License

MIT License - See [LICENSE](../LICENSE) for details.

This means anyone can:
- Use this code commercially
- Modify and distribute
- Use privately

With the requirement to:
- Include the original copyright notice
- Include the MIT license text

## Conclusion

Making ETPS open source aligns with its current purpose as a portfolio project. The real value lies in the knowledge, iteration speed, and execution capability demonstrated by building it - not in keeping the code secret.

If commercialization becomes relevant, the foundation is solid and the path forward is clear: fork, add premium features, and maintain the open source version as a community resource.

---

*Last updated: December 2024*

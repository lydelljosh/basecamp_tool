# Branch Cleanup: feature/attachments

## Decision: Delete feature/attachments branch

**Date**: 2025-08-11  
**Reason**: Redundant functionality - main branch already provides CLI-only operation

## Analysis

### What feature/attachments promised:
- CLI-based attachment downloading
- No browser interaction
- Complete todo data extraction

### What main branch already provides:
✅ CLI-only operation (after initial OAuth setup)  
✅ Complete todo/comment extraction  
✅ CSV export functionality  
✅ Uses existing access tokens from config.json

### What feature/attachments actually delivered:
✅ Enhanced debugging and metadata extraction  
✅ Attachment detection (filenames, sizes, blob IDs)  
❌ **No actual file downloads** (404 errors on all storage URLs)  
❌ **No meaningful improvement** over existing main branch functionality

## Technical Findings

### Basecamp Attachment Limitations Discovered:
- Storage URLs (`storage.3.basecamp.com`) require web session cookies
- API blob endpoints return 404 with OAuth tokens
- Vaults API not accessible with standard token scope
- SGID token resolution endpoints don't exist

### What Works:
- OAuth token authentication
- Todo/comment data extraction
- Attachment metadata detection
- CSV export generation

## Conclusion

The feature/attachments branch:
1. **Doesn't provide new functionality** - main already avoids browser interaction
2. **Can't deliver on core promise** - attachment downloads don't work
3. **Adds unnecessary complexity** - 900+ lines of code for metadata extraction
4. **Duplicates existing capabilities** - main.py already exports todo data

## Action Taken

Deleting feature/attachments branch because:
- Main branch already provides CLI-only todo export
- Attachment downloading is impossible via API alone
- Research documented the technical limitations
- No point maintaining redundant code

## Preserved Knowledge

Key learnings from this branch:
- Basecamp attachment URLs require web session authentication
- OAuth tokens don't provide access to storage endpoints
- bc-attachment elements contain rich metadata but not downloadable URLs
- SGID decoding possible but resolution endpoints missing

This research prevents future attempts at API-only attachment downloading.
# Quickstart: Episode Playlists

**Feature**: `/Users/eliassoares/Documents/projects/personal/malipod/specs/027-episode-playlists/spec.md`
**Date**: 2026-04-25

## Local dev

1. Run the app normally (existing workflow).
2. Register + login as a user.

## Manual verification

### Manage playlists

1. Open `GET /user/{your-nick}/playlists`.
2. Create a playlist via modal:
   - Name required
   - Description <= 1024
   - Optional image upload <= 1MB
3. Confirm playlist appears in list.
4. Edit the playlist and confirm changes persist.
5. Delete the playlist via confirmation modal; confirm it disappears.
6. Confirm Favorites appears as a read-only playlist and cannot be edited/deleted.

### Add to playlist from episode detail

1. Open an episode detail page `GET /episode/{id}`.
2. Click “Add to playlist”.
3. Select 2+ playlists and confirm.
4. Open each playlist and confirm the episode appears.

### Export/import

1. Export user data from profile page.
2. Create at least 1 playlist and add episodes.
3. Export again and confirm playlist sections are present.
4. Delete user data (or use a new user) and import snapshot.
5. Confirm playlists and memberships are restored; Favorites continues to work.

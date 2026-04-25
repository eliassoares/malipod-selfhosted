(function () {
  function safeJsonParse(value) {
    try {
      return JSON.parse(value);
    } catch (_) {
      return null;
    }
  }

  function formatTime(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    var s = Math.floor(seconds);
    var m = Math.floor(s / 60);
    var r = s % 60;
    return String(m) + ":" + String(r).padStart(2, "0");
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  var STORAGE_KEY = "maliplayer.state.v1";
  var META_KEY_PREFIX = "maliplayer.episode_meta.";

  function loadPersistedState() {
    var raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      var parsed = safeJsonParse(raw);
      if (parsed && typeof parsed === "object") return parsed;
    }
    if (window.__PLAYER_STATE__ && typeof window.__PLAYER_STATE__ === "object") {
      return window.__PLAYER_STATE__;
    }
    return null;
  }

  function persistState(state) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function persistEpisodeMeta(meta) {
    if (!meta || !meta.episodeId) return;
    sessionStorage.setItem(
      META_KEY_PREFIX + String(meta.episodeId),
      JSON.stringify(meta),
    );
  }

  function loadEpisodeMeta(episodeId) {
    var raw = sessionStorage.getItem(META_KEY_PREFIX + String(episodeId));
    if (!raw) return null;
    var parsed = safeJsonParse(raw);
    if (parsed && typeof parsed === "object") return parsed;
    return null;
  }

  function postJson(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "same-origin",
    });
  }

  function fetchEpisodeInfo(episodeId) {
    return fetch("/web/episode/" + String(episodeId) + "/info", {
      method: "GET",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    }).then(function (r) {
      if (!r.ok) throw new Error("episode info fetch failed");
      return r.json();
    });
  }

  var audio = document.getElementById("maliplayer-audio");
  var cover = document.getElementById("maliplayer-cover");
  var title = document.getElementById("maliplayer-episode-title");
  var subtitle = document.getElementById("maliplayer-podcast-title");
  var progress = document.getElementById("maliplayer-progress");
  var fill = document.getElementById("maliplayer-progress-fill");
  var timeCur = document.getElementById("maliplayer-time-current");
  var timeTotal = document.getElementById("maliplayer-time-total");
  var btnRewind = document.getElementById("maliplayer-rewind");
  var btnFwd = document.getElementById("maliplayer-forward");
  var btnPlayPause = document.getElementById("maliplayer-play-pause");
  var playIcon = document.getElementById("maliplayer-play-icon");

  if (!audio || !progress || !btnPlayPause) {
    return;
  }

  var state = {
    episodeId: null,
    positionSec: null,
    queueMode: null,
    queueRefId: null,
    queueIds: [],
    queueIndex: 0,
    startedSec: null,
    lastStateSentAt: 0,
  };

  function setEmptyUi() {
    var emptyTitle = title && title.dataset ? title.dataset.emptyTitle : null;
    var emptySubtitle =
      subtitle && subtitle.dataset ? subtitle.dataset.emptySubtitle : null;
    if (title) title.textContent = emptyTitle || "No episode selected";
    if (subtitle) subtitle.textContent = emptySubtitle || "Start from an episode";
    if (cover) cover.src = "/static/placeholders/malte.png";
    if (fill) fill.style.width = "0%";
    if (timeCur) timeCur.textContent = "0:00";
    if (timeTotal) timeTotal.textContent = "0:00";
    if (playIcon) playIcon.textContent = "play_arrow";
  }

  function applyMeta(meta) {
    if (title) title.textContent = meta.episodeTitle || "";
    if (subtitle) subtitle.textContent = meta.podcastTitle || "";
    if (cover && meta.coverUrl) cover.src = meta.coverUrl;
  }

  function updateProgressUi() {
    var current = audio.currentTime || 0;
    var total = audio.duration || 0;
    if (timeCur) timeCur.textContent = formatTime(current);
    if (timeTotal) timeTotal.textContent = formatTime(total);
    var pct = 0;
    if (Number.isFinite(total) && total > 0) {
      pct = (current / total) * 100;
    }
    if (fill) fill.style.width = String(clamp(pct, 0, 100)) + "%";
  }

  function sendState(throttled) {
    if (!state.episodeId) return;
    var now = Date.now();
    if (throttled && now - state.lastStateSentAt < 10000) return;
    state.lastStateSentAt = now;
    postJson("/web/player/state", {
      episode_id: state.episodeId,
      position_sec: Math.floor(audio.currentTime || 0),
      queue_mode: state.queueMode,
      queue_ref_id: state.queueRefId,
    }).catch(function () {});
  }

  function sendAction(action) {
    if (!state.episodeId) return;
    var total = audio.duration;
    if (!Number.isFinite(total) || total <= 0) return;
    var payload = {
      episode_id: state.episodeId,
      action: action,
    };
    if (action === "play" || action === "pause") {
      payload.started = state.startedSec != null ? state.startedSec : 0;
      payload.position = Math.floor(audio.currentTime || 0);
      payload.total = Math.floor(total);
    }
    postJson("/web/player/action", payload).catch(function () {});
  }

  function loadEpisode(episodeId, startSec, meta, paused) {
    if (!episodeId) return;
    state.episodeId = episodeId;
    state.positionSec = startSec != null ? startSec : 0;

    var metaObj = meta || loadEpisodeMeta(episodeId);
    var promise;
    if (metaObj && metaObj.mediaUrl) {
      promise = Promise.resolve(metaObj);
    } else {
      promise = fetchEpisodeInfo(episodeId).then(function (info) {
        return {
          episodeId: info.episode_id,
          feedId: info.feed_id,
          mediaUrl: info.media_url,
          episodeTitle: info.episode_title,
          podcastTitle: info.podcast_title,
          coverUrl: info.cover_url,
        };
      });
    }

    return promise
      .then(function (resolved) {
        if (!resolved.mediaUrl) {
          throw new Error("missing media url");
        }
        persistEpisodeMeta(resolved);
        applyMeta(resolved);
        audio.src = resolved.mediaUrl;
        audio.currentTime = startSec || 0;
        updateProgressUi();
        if (!paused) {
          return audio.play();
        }
        return undefined;
      })
      .catch(function () {});
  }

  function seekTo(seconds) {
    if (!state.episodeId) return;
    var total = audio.duration;
    if (!Number.isFinite(total) || total <= 0) return;
    audio.currentTime = clamp(seconds, 0, total);
    updateProgressUi();
    sendState(false);
  }

  function setQueue(ids, mode, refId) {
    state.queueMode = mode || null;
    state.queueRefId = refId != null ? refId : null;
    state.queueIds = Array.isArray(ids) ? ids.slice() : [];
    state.queueIndex = 0;
    persistState({
      episodeId: state.episodeId,
      positionSec: state.positionSec,
      queueMode: state.queueMode,
      queueRefId: state.queueRefId,
      queueIds: state.queueIds,
      queueIndex: state.queueIndex,
    });
  }

  function nextEpisode() {
    if (!state.episodeId) return;
    if (state.queueMode === "playlist") {
      var nextIndex = (state.queueIndex || 0) + 1;
      if (!state.queueIds || nextIndex >= state.queueIds.length) {
        audio.pause();
        return;
      }
      state.queueIndex = nextIndex;
      var nextId = state.queueIds[nextIndex];
      state.startedSec = 0;
      loadEpisode(nextId, 0, null, false);
      persistState({
        episodeId: nextId,
        positionSec: 0,
        queueMode: state.queueMode,
        queueRefId: state.queueRefId,
        queueIds: state.queueIds,
        queueIndex: state.queueIndex,
      });
      return;
    }

    fetch("/web/episode/" + String(state.episodeId) + "/next", {
      method: "GET",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    })
      .then(function (r) {
        if (!r.ok) throw new Error("next fetch failed");
        return r.json();
      })
      .then(function (data) {
        if (!data || !data.episode_id) {
          audio.pause();
          return;
        }
        var nextId = data.episode_id;
        state.queueIds = Array.isArray(state.queueIds) ? state.queueIds : [];
        state.queueIds.push(nextId);
        state.queueIndex = state.queueIds.length - 1;
        state.startedSec = 0;
        loadEpisode(nextId, 0, null, false);
        persistState({
          episodeId: nextId,
          positionSec: 0,
          queueMode: state.queueMode,
          queueRefId: state.queueRefId,
          queueIds: state.queueIds,
          queueIndex: state.queueIndex,
        });
      })
      .catch(function () {});
  }

  audio.addEventListener("timeupdate", function () {
    updateProgressUi();
    if (!audio.paused) {
      sendState(true);
    }
  });

  audio.addEventListener("play", function () {
    state.startedSec = Math.floor(audio.currentTime || 0);
    if (playIcon) playIcon.textContent = "pause";
    sendAction("play");
  });

  audio.addEventListener("pause", function () {
    if (playIcon) playIcon.textContent = "play_arrow";
    sendState(false);
    if (state.startedSec != null) {
      sendAction("pause");
    }
  });

  audio.addEventListener("ended", function () {
    sendState(false);
    sendAction("play");
    nextEpisode();
  });

  btnPlayPause.addEventListener("click", function () {
    if (!state.episodeId) return;
    if (audio.paused) {
      audio.play().catch(function () {});
      return;
    }
    audio.pause();
  });

  if (btnRewind) {
    btnRewind.addEventListener("click", function () {
      seekTo((audio.currentTime || 0) - 15);
    });
  }

  if (btnFwd) {
    btnFwd.addEventListener("click", function () {
      seekTo((audio.currentTime || 0) + 30);
    });
  }

  progress.addEventListener("click", function (event) {
    var rect = progress.getBoundingClientRect();
    var x = event.clientX - rect.left;
    var pct = x / rect.width;
    var total = audio.duration || 0;
    if (!Number.isFinite(total) || total <= 0) return;
    seekTo(total * pct);
  });

  window.addEventListener("beforeunload", function () {
    var currentPos = Math.floor(audio.currentTime || 0);
    persistState({
      episodeId: state.episodeId,
      positionSec: currentPos,
      queueMode: state.queueMode,
      queueRefId: state.queueRefId,
      queueIds: state.queueIds,
      queueIndex: state.queueIndex,
      isPlaying: !audio.paused,
    });
    if (state.episodeId && !audio.paused) {
      var total = audio.duration;
      if (Number.isFinite(total) && total > 0 && state.startedSec != null) {
        var actionPayload = JSON.stringify({
          episode_id: state.episodeId,
          action: "pause",
          started: state.startedSec,
          position: currentPos,
          total: Math.floor(total),
        });
        navigator.sendBeacon(
          "/web/player/action",
          new Blob([actionPayload], { type: "application/json" }),
        );
      }
    }
  });

  document.querySelectorAll("[data-maliplayer-play-episode]").forEach(function (el) {
    el.addEventListener("click", function () {
      var episodeId = parseInt(el.dataset.episodeId || "0", 10);
      if (!episodeId) return;
      if (el.dataset.mediaUrl === "") return;
      var start = parseInt(el.dataset.startSec || "0", 10) || 0;
      var feedId = parseInt(el.dataset.feedId || "0", 10) || null;
      state.queueMode = "podcast";
      state.queueRefId = feedId;
      state.queueIds = [episodeId];
      state.queueIndex = 0;
      var meta = {
        episodeId: episodeId,
        feedId: feedId,
        mediaUrl: el.dataset.mediaUrl,
        episodeTitle: el.dataset.episodeTitle,
        podcastTitle: el.dataset.podcastTitle,
        coverUrl: el.dataset.coverUrl,
      };
      persistEpisodeMeta(meta);
      loadEpisode(episodeId, start, meta, false);
      persistState({
        episodeId: episodeId,
        positionSec: start,
        queueMode: state.queueMode,
        queueRefId: state.queueRefId,
        queueIds: state.queueIds,
        queueIndex: state.queueIndex,
      });
    });
  });

  document
    .querySelectorAll("[data-maliplayer-play-playlist]")
    .forEach(function (el) {
      el.addEventListener("click", function () {
        var raw = el.dataset.episodeIds || "";
        var ids = raw
          .split(",")
          .map(function (part) {
            return parseInt(part, 10);
          })
          .filter(function (n) {
            return Number.isFinite(n) && n > 0;
          });
        if (!ids.length) return;
        var playlistId = parseInt(el.dataset.playlistId || "0", 10) || null;
        state.queueMode = "playlist";
        state.queueRefId = playlistId;
        state.queueIds = ids;
        state.queueIndex = 0;
        state.startedSec = 0;
        loadEpisode(ids[0], 0, null, false);
        persistState({
          episodeId: ids[0],
          positionSec: 0,
          queueMode: state.queueMode,
          queueRefId: state.queueRefId,
          queueIds: state.queueIds,
          queueIndex: state.queueIndex,
        });
      });
    });

  window.MaliPlayer = {
    load: function (episodeId, startSec) {
      return loadEpisode(episodeId, startSec || 0, null, true);
    },
    play: function () {
      return audio.play();
    },
    pause: function () {
      audio.pause();
    },
    seek: function (sec) {
      seekTo(sec);
    },
    next: function () {
      nextEpisode();
    },
    setQueue: function (ids, mode, refId) {
      setQueue(ids, mode, refId);
    },
  };

  setEmptyUi();
  var persisted = loadPersistedState();
  if (persisted && persisted.episodeId) {
    state.queueMode = persisted.queueMode || null;
    state.queueRefId = persisted.queueRefId != null ? persisted.queueRefId : null;
    state.queueIds = Array.isArray(persisted.queueIds) ? persisted.queueIds : [];
    state.queueIndex = persisted.queueIndex || 0;
    var startSec = persisted.positionSec || 0;
    var wasPaused = !persisted.isPlaying;
    loadEpisode(persisted.episodeId, startSec, null, wasPaused);
  }
})();

// Citizen Dashboard Enhancements - Reports, Details, Upvote
document.addEventListener('DOMContentLoaded', function() {
  if (!['citizen', 'home', 'officer'].includes(window.CIVIC_PAGE)) return;

  // Modal elements
  const modal = document.getElementById('issue-modal');
  const closeBtn = document.getElementById('close-modal');
  const upvoteBtn = document.getElementById('upvote-btn');
  const aiInsightsBox = document.getElementById('modal-ai-insights');
  const aiSummary = document.getElementById('modal-ai-summary');
  const aiImpact = document.getElementById('modal-ai-impact');
  const aiDepartment = document.getElementById('modal-ai-department');
  const aiSeverity = document.getElementById('modal-ai-severity');
  const aiActions = document.getElementById('modal-ai-actions');
  const workProofContainer = document.getElementById('modal-work-proof');
  const workProofUpload = document.getElementById('work-proof-upload');
  const workProofPreviews = document.getElementById('work-proof-previews');
  const workProofNote = document.getElementById('work-proof-note');
  const submitWorkProofBtn = document.getElementById('submit-work-proof');
  if (!modal || !closeBtn || !upvoteBtn) return;
  let pendingWorkProofImages = [];

  // Close modal
  function closeModal() {
    modal.classList.add('hidden');
  }

  closeBtn.onclick = closeModal;
  modal.onclick = function(e) {
    if (e.target === modal) closeModal();
  };

  const renderWorkProofPreviews = () => {
    if (!workProofPreviews) return;
    workProofPreviews.innerHTML = pendingWorkProofImages
      .map((img, idx) => `
        <div class="relative group">
          <img src="${img}" class="w-full h-28 object-cover rounded-lg border border-slate-700" alt="Work proof preview ${idx + 1}">
          <button type="button" class="absolute top-2 right-2 bg-black/70 text-white rounded-md px-2 py-1 text-xs remove-work-proof" data-idx="${idx}">X</button>
        </div>
      `)
      .join('');

    workProofPreviews.querySelectorAll('.remove-work-proof').forEach((button) => {
      button.addEventListener('click', (event) => {
        event.preventDefault();
        pendingWorkProofImages.splice(Number(button.dataset.idx), 1);
        renderWorkProofPreviews();
      });
    });
  };

  // Load issue details
  async function loadIssueDetail(issueId) {
    try {
      Civic.setLoading(true);
      const data = await Civic.API.req(`/api/issues/${issueId}/`);

      document.getElementById('modal-title').textContent = data.title || 'No Title';
      document.getElementById('modal-code').textContent = data.issue_code || 'N/A';
      document.getElementById('modal-status').textContent = data.status || 'Unknown';
      document.getElementById('modal-status').className = `status-pill ${Civic.getStatusColor(data.status || 'Submitted')}`;
      document.getElementById('modal-priority').textContent = `Priority ${data.priority || 0}`;
      document.getElementById('modal-description').textContent = data.description || 'No description';
      document.getElementById('modal-location').textContent = data.location?.address || 'Location unknown';
      document.getElementById('modal-upvotes').textContent = data.upvote_count || 0;
      document.getElementById('modal-date').textContent = `Created ${new Date(data.created_at).toLocaleDateString()}`;

      if (aiInsightsBox && data.ai_insights) {
        aiSummary.textContent = data.ai_insights.summary || 'No AI summary available';
        aiImpact.textContent = data.ai_insights.impact || '';
        aiDepartment.textContent = data.ai_insights.department || 'Municipal Operations';
        aiSeverity.textContent = (data.ai_insights.severity || 'medium').toUpperCase();
        aiActions.innerHTML = (data.ai_insights.recommended_actions || [])
          .map(action => `<li class="rounded-xl bg-slate-950/40 px-3 py-2">${Civic.escapeHtml(action)}</li>`)
          .join('');
        aiInsightsBox.classList.remove('hidden');
      } else if (aiInsightsBox) {
        aiInsightsBox.classList.add('hidden');
        aiActions.innerHTML = '';
      }

      if (workProofContainer) {
        const proofEntries = Array.isArray(data.work_proof) ? data.work_proof : [];
        if (proofEntries.length > 0) {
          workProofContainer.innerHTML = proofEntries
            .flatMap((entry) => (entry.photos || []).map((photo) => `
              <img src="${photo}" class="w-full h-32 object-cover rounded-lg cursor-pointer hover:shadow-lg" alt="Work proof photo" onclick="window.open(this.src)">
            `))
            .join('');
        } else {
          workProofContainer.innerHTML = '<p class="text-slate-400 col-span-full text-center py-8">No work proof uploaded yet</p>';
        }
      }

      // Photos
      const photosContainer = document.getElementById('modal-photos');
      if (data.photos && data.photos.length > 0) {
        photosContainer.innerHTML = data.photos.slice(0, 6).map(photo => 
          `<img src="${photo}" class="w-full h-32 object-cover rounded-lg cursor-pointer hover:shadow-lg" alt="Photo" onclick="window.Civic.showLightbox(this.src)">`
        ).join('');
      } else {
        photosContainer.innerHTML = '<p class="text-slate-400 col-span-full text-center py-8">No photos attached</p>';
      }

      // Upvote button state
      upvoteBtn.textContent = data.upvoted ? 'Remove upvote' : 'Upvote';
      upvoteBtn.dataset.issueId = issueId;
      upvoteBtn.dataset.upvoted = data.upvoted;
      if (submitWorkProofBtn) {
        submitWorkProofBtn.dataset.issueId = issueId;
      }

      modal.classList.remove('hidden');
    } catch (error) {
      Civic.toast(error.message || 'Failed to load issue details', 'err');
    } finally {
      Civic.setLoading(false);
    }
  }

  // Upvote toggle
  upvoteBtn.onclick = async function() {
    if (!Civic.API.user) {
      Civic.toast('Sign in to upvote issues', 'err');
      window.location.href = '/login/';
      return;
    }

    const issueId = this.dataset.issueId;
    const isUpvoted = this.dataset.upvoted === 'true';
    
    try {
      Civic.setLoading(true);
      await Civic.API.req(`/api/issues/${issueId}/upvote/`, { method: 'POST' });
      
      // Reload detail
      await loadIssueDetail(issueId);
      Civic.toast(isUpvoted ? 'Upvote removed' : 'Upvoted', 'ok');
    } catch (error) {
      Civic.toast(error.message || 'Upvote failed', 'err');
    } finally {
      Civic.setLoading(false);
    }
  };

  // Wait for issues loaded, then add click handlers
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) { // Element
          const cards = node.matches?.('.issue-card') ? [node] : (node.querySelectorAll ? node.querySelectorAll('.issue-card') : []);
          cards.forEach(card => {
            if (!card.dataset.detailBound) {
              card.dataset.detailBound = 'true';
              card.onclick = (event) => {
                if (event.target.closest('button, a, input, textarea, select')) return;
                loadIssueDetail(card.dataset.issueId || card.closest('[data-id]')?.dataset.id);
              };
              card.style.cursor = 'pointer';
              card.classList.add('hover:shadow-lg', 'transition-shadow');
            }
          });
        }
      });
    });
  });

  const reportsContainer = document.getElementById('my-reports');
  if (reportsContainer) {
    observer.observe(reportsContainer, { childList: true, subtree: true });
  }

  const homeIssuesContainer = document.getElementById('home-issues');
  if (homeIssuesContainer) {
    observer.observe(homeIssuesContainer, { childList: true, subtree: true });
  }

  const kanbanContainer = document.getElementById('kanban');
  if (kanbanContainer) {
    observer.observe(kanbanContainer, { childList: true, subtree: true });
  }

  document.querySelectorAll('.issue-card').forEach((card) => {
    if (!card.dataset.detailBound) {
      card.dataset.detailBound = 'true';
      card.onclick = (event) => {
        if (event.target.closest('button, a, input, textarea, select')) return;
        loadIssueDetail(card.dataset.issueId || card.closest('[data-id]')?.dataset.id || card.dataset.id);
      };
      card.style.cursor = 'pointer';
    }
  });

  if (workProofUpload) {
    workProofUpload.addEventListener('change', (event) => {
      const files = Array.from(event.target.files || []);
      const toAdd = files.slice(0, 5 - pendingWorkProofImages.length);
      toAdd.forEach((file) => {
        const reader = new FileReader();
        reader.onload = (loadEvent) => {
          pendingWorkProofImages.push(loadEvent.target.result);
          renderWorkProofPreviews();
        };
        reader.readAsDataURL(file);
      });
    });
  }

  if (submitWorkProofBtn) {
    submitWorkProofBtn.addEventListener('click', async () => {
      if (!Civic.API.user || !['officer', 'admin'].includes(Civic.API.user.role)) {
        Civic.toast('Only officers or admins can upload work proof', 'err');
        return;
      }

      const issueId = submitWorkProofBtn.dataset.issueId;
      if (!issueId) {
        Civic.toast('Open an issue first', 'err');
        return;
      }
      if (pendingWorkProofImages.length === 0) {
        Civic.toast('Add at least one work photo', 'err');
        return;
      }

      try {
        Civic.setLoading(true);
        await Civic.API.req(`/api/issues/${issueId}/work-proof/`, {
          method: 'POST',
          body: JSON.stringify({
            photos: pendingWorkProofImages,
            note: workProofNote?.value || '',
          }),
        });
        pendingWorkProofImages = [];
        if (workProofNote) workProofNote.value = '';
        renderWorkProofPreviews();
        Civic.toast('Work proof uploaded for verification', 'ok');
        await loadIssueDetail(issueId);
      } catch (error) {
        Civic.toast(error.message || 'Failed to upload work proof', 'err');
      } finally {
        Civic.setLoading(false);
      }
    });
  }

  // Load more button (if needed later)
  const loadMoreBtn = document.getElementById('load-more-reports');
  if (loadMoreBtn) {
    loadMoreBtn.onclick = async () => {
      // Implement pagination later
      Civic.toast('More reports loading... (coming soon)', 'ok');
    };
  }
});

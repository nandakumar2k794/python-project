const steps=[...document.querySelectorAll('.wizard-step')];const chips=[...document.querySelectorAll('#report-stepper .step')];let index=0;
const categories=["Roads","Water","Sanitation","Electricity","Parks","Street Lights","Encroachment","Others"];
const priorities=["Low","Medium","High","Critical"];
let uploadedMedia=[];

const sync=()=>{
  steps.forEach((s,i)=>{
    s.classList.toggle('hidden',i!==index);
    s.style.animation=i===index?'slideIn 300ms ease-out':'none';
  });
  chips.forEach((c,i)=>{
    c.classList.toggle('active',i===index);
    if(i===index)c.style.animation='bounce 400ms ease-out';
  });
  document.getElementById('prev-step').disabled=index===0;
  document.getElementById('next-step').classList.toggle('hidden',index===steps.length-1);
  document.getElementById('submit-report').classList.toggle('hidden',index!==steps.length-1);
};

const validateStep=(stepIndex)=>{
  const step=steps[stepIndex];
  if(!step)return true;
  
  switch(stepIndex){
    case 0:{
      const cat=step.querySelector('[name="category"]');
      return cat&&cat.value;
    }
    case 1:{
      const addr=step.querySelector('[name="address"]');
      return addr&&addr.value.trim().length>3;
    }
    case 2:{
      // Accept if at least one image or video is uploaded
      return (window.uploadedImages?.length > 0) || (window.uploadedVideos?.length > 0);
    }
    case 3:{
      const title=step.querySelector('[name="title"]');
      const desc=step.querySelector('[name="description"]');
      return title&&title.value.trim().length>2&&desc&&desc.value.trim().length>5;
    }
  }
  return true;
};

const showValidationError=(msg)=>{
  if(window.Civic && window.Civic.toast){
    window.Civic.toast(msg,"err",3000);
  }else{
    alert(msg);
    console.error('Form validation:', msg);
  }
};

document.getElementById('next-step')?.addEventListener('click',()=>{
  if(!validateStep(index)){
    const msgs=["Please select a category","Please enter an address","Please upload at least one photo or video","Title and description are required",""];
    showValidationError(msgs[index]);
    return;
  }
  if(index<steps.length-1){
    index++;
    sync();
    window.scrollTo({top:0,behavior:'smooth'});
  }
});

document.getElementById('prev-step')?.addEventListener('click',()=>{
  if(index>0){
    index--;
    sync();
    window.scrollTo({top:0,behavior:'smooth'});
  }
});

const parseCoordinates=(input)=>{
  const num=Number(input);
  return !isNaN(num)?num:0;
};

document.getElementById('report-form')?.addEventListener('submit',async(e)=>{
  e.preventDefault();
  
  if(!validateStep(index)){
    showValidationError("Please complete all required fields");
    return;
  }
  
  Civic.setLoading(true);
  try{
    const f=new FormData(e.target);
    const urlMedia=String(f.get('media')||'').split('\n').map(s=>s.trim()).filter(Boolean).slice(0,5);
    // Always include uploaded images/videos (base64) and URLs
    const allMedia=[...(window.uploadedImages||[]),...(window.uploadedVideos||[]),...urlMedia].slice(0,5);
    const lat=parseCoordinates(f.get('lat')||'12.9716');
    const lng=parseCoordinates(f.get('lng')||'77.5946');

    // Always use the current values in the form (AI-generated or user-edited)
    const title=(f.get('title')||'').trim();
    const desc=(f.get('description')||'').trim();
    const addr=(f.get('address')||'').trim();
    const cat=f.get('category')||'Others';

    const payload={
      category:cat,
      title:title,
      description:desc,
      location:{
        address:addr,
        lat:lat,
        lng:lng
      },
      photos:allMedia,
      priority:0
    };

    if(!payload.title||payload.title.length<3)throw new Error("Title must be at least 3 characters");
    if(!payload.description||payload.description.length<10)throw new Error("Description must be at least 10 characters");

    const out=await Civic.API.req('/api/issues/',{
      method:'POST',
      body:JSON.stringify(payload)
    });

    if(!out.issue_code)throw new Error("Issue creation failed");
    Civic.toast(`Issue submitted: ${out.issue_code}`,'ok',3000);

    setTimeout(()=>{
      window.location.href='/citizen/';
    },1000);
  }catch(err){
    showValidationError(err.message||"Failed to submit issue");
  }finally{
    Civic.setLoading(false);
  }
});

sync();

const aiImproveBtn = document.getElementById('ai-improve-report');
const aiFeedback = document.getElementById('ai-report-feedback');

if (aiImproveBtn) {
  aiImproveBtn.addEventListener('click', async () => {
    const form = document.getElementById('report-form');
    if (!form || !window.Civic?.API) return;

    // Validate user is authenticated
    if (!window.Civic.API.token) {
      showValidationError('You must be logged in to use AI features. Please log in and try again.');
      return;
    }

    const title = (form.querySelector('[name="title"]')?.value || '').trim();
    const description = (form.querySelector('[name="description"]')?.value || '').trim();
    const address = (form.querySelector('[name="address"]')?.value || '').trim();
    const category = form.querySelector('[name="category"]')?.value || 'Others';

    if (!description) {
      showValidationError('Write a description first, then AI can improve it.');
      return;
    }

    aiImproveBtn.disabled = true;
    const originalLabel = aiImproveBtn.textContent;
    aiImproveBtn.textContent = 'Improving...';

    try {
      const result = await window.Civic.API.req('/api/dashboard/ai/report-assist/', {
        method: 'POST',
        body: JSON.stringify({ title, description, address, category }),
      });

    if (result.improved_title) {
        form.querySelector('[name="title"]').value = result.improved_title;
      }
      if (result.improved_description) {
        form.querySelector('[name="description"]').value = result.improved_description;
      }
      if (result.suggested_category) {
        form.querySelector('[name="category"]').value = result.suggested_category;
      }

      if (aiFeedback) {
        const questions = Array.isArray(result.questions) && result.questions.length > 0
          ? `<div class="mt-2"><strong>Helpful follow-ups:</strong><ul class="mt-2 space-y-1">${result.questions.map(q => `<li>- ${window.Civic.escapeHtml(q)}</li>`).join('')}</ul></div>`
          : '';
        aiFeedback.innerHTML = `
          <div><strong>AI suggestion:</strong> ${window.Civic.escapeHtml(result.summary || 'Report improved for clarity.')}</div>
          <div class="mt-2">Suggested category: <strong>${window.Civic.escapeHtml(result.suggested_category || category)}</strong> | Priority: <strong>${result.priority || 3}</strong></div>
          ${questions}
        `;
        aiFeedback.classList.remove('hidden');
      }

      window.Civic.toast('AI improved your report draft', 'ok', 2500);
    } catch (error) {
      const errorMsg = error.message || 'AI improvement failed';
      
      // Handle different error types
      let displayMsg = errorMsg;
      if (errorMsg.includes('403') || errorMsg.includes('Forbidden') || 
          errorMsg.includes('Authentication credentials') || errorMsg.includes('401')) {
        displayMsg = 'Session expired or not authenticated. Please log out and log back in to use AI features.';
      } else if (errorMsg.includes('429') || errorMsg.includes('rate limit') || errorMsg.includes('Too Many Requests')) {
        displayMsg = 'AI service is temporarily busy. Please try again later.';
      } else if (errorMsg.includes('timeout') || errorMsg.includes('504')) {
        displayMsg = 'AI service is taking too long. Please try again later.';
      }
      
      showValidationError(displayMsg);
    } finally {
      aiImproveBtn.disabled = false;
      aiImproveBtn.textContent = originalLabel;
    }
  });
}


// --- Image compression helper ---
const compressImage = (base64Image, maxWidth = 800, maxHeight = 800, quality = 0.75) => {
  return new Promise((resolve) => {
    // Skip compression for small images (< 50KB base64 ≈ 37KB binary)
    if (base64Image.length < 68000) {
      console.log('Image small enough, skipping compression');
      resolve(base64Image);
      return;
    }
    
    const img = new Image();
    img.onload = () => {
      let { width, height } = img;
      
      // Only resize if image is larger than max dimensions
      const needsResize = width > maxWidth || height > maxHeight;
      
      if (!needsResize && base64Image.length < 200000) {
        // Image is small and within dimensions, keep original
        console.log('Image within size limits, skipping compression');
        resolve(base64Image);
        return;
      }
      
      // Calculate new dimensions while maintaining aspect ratio
      if (needsResize) {
        const ratio = Math.min(maxWidth / width, maxHeight / height);
        width = Math.round(width * ratio);
        height = Math.round(height * ratio);
      }
      
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);
      
      // Compress as JPEG
      const compressed = canvas.toDataURL('image/jpeg', quality);
      
      // Only use compressed if it's actually smaller
      if (compressed.length < base64Image.length) {
        const originalSize = Math.round(base64Image.length * 0.75 / 1024);
        const compressedSize = Math.round(compressed.length * 0.75 / 1024);
        console.log(`Image compressed: ${originalSize}KB -> ${compressedSize}KB (${Math.round(compressedSize/originalSize*100)}%)`);
        resolve(compressed);
      } else {
        console.log('Compressed image larger than original, using original');
        resolve(base64Image);
      }
    };
    img.onerror = () => resolve(base64Image); // Fallback to original
    img.src = base64Image;
  });
};

// --- Image/Video upload handling ---
const photoInput = document.getElementById('photo-upload');
const mediaPreviews = document.getElementById('media-previews');
window.uploadedImages = [];
window.uploadedVideos = [];

const renderMediaPreviews = () => {
  mediaPreviews.innerHTML = '';
  uploadedImages.slice(0, 5).forEach((img, idx) => {
    const div = document.createElement('div');
    div.className = 'relative group';
    div.innerHTML = `
      <img src="${img}" class="w-full h-40 object-cover rounded-lg border border-slate-700 group-hover:border-blue-500 transition-all" alt="Preview ${idx + 1}">
      <button type="button" class="absolute top-2 right-2 bg-red-500/80 hover:bg-red-600 text-white p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity" data-idx="${idx}" title="Remove image">X</button>
    `;
    const btn = div.querySelector('button');
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      uploadedImages.splice(idx, 1);
      renderMediaPreviews();
    });
    mediaPreviews.appendChild(div);
  });
  uploadedVideos.slice(0, 5 - uploadedImages.length).forEach((vid, idx) => {
    const div = document.createElement('div');
    div.className = 'relative group';
    div.innerHTML = `
      <video src="${vid}" controls class="w-full h-40 object-cover rounded-lg border border-slate-700 group-hover:border-blue-500 transition-all"></video>
      <button type="button" class="absolute top-2 right-2 bg-red-500/80 hover:bg-red-600 text-white p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity" data-vidx="${idx}" title="Remove video">X</button>
    `;
    const btn = div.querySelector('button');
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      uploadedVideos.splice(idx, 1);
      renderMediaPreviews();
    });
    mediaPreviews.appendChild(div);
  });
};

if (photoInput) {
  photoInput.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files || []);
    for (const file of files) {
      if (file.type.startsWith('image/')) {
        if (uploadedImages.length < 5) {
          const reader = new FileReader();
          reader.onload = async (event) => {
            // Compress image before storing
            const compressed = await compressImage(event.target.result, 800, 800, 0.75);
            uploadedImages.push(compressed);
            renderMediaPreviews();
          };
          reader.readAsDataURL(file);
        }
      } else if (file.type.startsWith('video/')) {
        if (uploadedVideos.length < 5) {
          const reader = new FileReader();
          reader.onload = (event) => {
            uploadedVideos.push(event.target.result);
            renderMediaPreviews();
          };
          reader.readAsDataURL(file);
        }
      }
    }
  });

  // Paste image support
  document.addEventListener('paste', async (e) => {
    const items = e.clipboardData?.items || [];
    for (const item of Array.from(items)) {
      if (item.type.includes('image')) {
        e.preventDefault();
        const blob = item.getAsFile();
        if (blob && uploadedImages.length < 5) {
          const reader = new FileReader();
          reader.onload = async (event) => {
            // Compress pasted image too
            const compressed = await compressImage(event.target.result, 800, 800, 0.75);
            uploadedImages.push(compressed);
            renderMediaPreviews();
            Civic.toast('Image pasted and compressed', 'ok', 2000);
          };
          reader.readAsDataURL(blob);
        }
      }
    }
  });
}

// --- AI Description from Media ---
const aiDescribeBtn = document.getElementById('ai-describe-from-media');
const aiMediaFeedback = document.getElementById('ai-media-feedback');
const aiMediaMessage = document.getElementById('ai-media-message');

if (aiDescribeBtn) {
  aiDescribeBtn.addEventListener('click', async () => {
    // Validate user is authenticated
    if (!window.Civic.API.token) {
      showValidationError('You must be logged in to use AI features. Please log in and try again.');
      return;
    }
    
    if (!uploadedImages.length) {
      showValidationError('Please upload at least one image for AI to analyze.');
      return;
    }
    aiDescribeBtn.disabled = true;
    aiDescribeBtn.textContent = 'Analyzing...';
    aiMediaFeedback.classList.remove('hidden');
    aiMediaMessage.textContent = 'Analyzing image with AI...';
    try {
      // Get form data for better context
      const form = document.getElementById('report-form');
      const category = form.querySelector('[name="category"]')?.value || '';
      const address = form.querySelector('[name="address"]')?.value || '';
      
      // Send the first image (base64) to the backend with context
      const result = await window.Civic.API.req('/api/dashboard/ai/describe-issue/', {
        method: 'POST',
        body: JSON.stringify({ 
          image: uploadedImages[0],
          category: category,
          address: address
        })
      });
      
      // Verify response has required fields
      if (!result) {
        throw new Error('Empty response from AI service');
      }

      // Set title and description if provided
      if (result.title) {
        form.querySelector('[name="title"]').value = result.title;
        console.log('Title set:', result.title);
      } else {
        console.warn('No title in response:', result);
      }
      
      if (result.description) {
        form.querySelector('[name="description"]').value = result.description;
        console.log('Description set:', result.description);
      } else {
        console.warn('No description in response:', result);
      }
      
      // Display feedback
      const feedbackText = result.summary || 'AI generated a suggestion.';
      aiMediaMessage.textContent = feedbackText;
      console.log('AI Feedback:', feedbackText);
      
      window.Civic.toast('AI generated a description from your image.', 'ok', 2500);
    } catch (err) {
      const errorMsg = err.message || 'AI analysis failed. Please provide a manual description.';
      
      // Handle different error types
      let displayMsg = errorMsg;
      
      // Check if it's an authentication error
      if (errorMsg.includes('403') || errorMsg.includes('Forbidden') || 
          errorMsg.includes('Authentication credentials') || errorMsg.includes('401')) {
        displayMsg = 'Session expired or not authenticated. Please log out and log back in to use AI features.';
      }
      // Check if it's a rate limit error
      else if (errorMsg.includes('429') || errorMsg.includes('rate limit') || errorMsg.includes('Too Many Requests')) {
        displayMsg = 'AI service is temporarily busy. Please wait a moment and try again, or provide a manual description.';
      }
      // Check if it's a timeout
      else if (errorMsg.includes('timeout') || errorMsg.includes('504')) {
        displayMsg = 'Image analysis is taking too long. Please provide a manual description or try again later.';
      }
      
      aiMediaMessage.textContent = displayMsg;
      console.error('AI describe error:', err);
      showValidationError(displayMsg);
    } finally {
      aiDescribeBtn.disabled = false;
      aiDescribeBtn.textContent = '✨ Generate Description from Media';
    }
  });
}

// Current location button
const useLocationBtn=document.getElementById('use-current-location');
if(useLocationBtn){
  useLocationBtn.addEventListener('click',(e)=>{
    e.preventDefault();
    useLocationBtn.disabled=true;
    useLocationBtn.textContent='Getting location...';
    
    if(!navigator.geolocation){
      Civic.toast('Geolocation not supported','err',3000);
      useLocationBtn.disabled=false;
      useLocationBtn.textContent='Use Current Location';
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      (position)=>{
        const {latitude,longitude}=position.coords;
        const form=document.getElementById('report-form');
        form.querySelector('[name="lat"]').value=latitude.toFixed(4);
        form.querySelector('[name="lng"]').value=longitude.toFixed(4);
        
        // Try to get address from coordinates using reverse geocoding
        fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
          .then(r=>r.json())
          .then(data=>{
            const address=data.address?.road||data.address?.suburb||data.address?.village||data.address?.town||'Current Location';
            form.querySelector('[name="address"]').value=address;
            Civic.toast(`Location set to ${address}`,'ok',3000);
          })
          .catch(()=>{
            form.querySelector('[name="address"]').value=`Lat: ${latitude.toFixed(4)}, Lng: ${longitude.toFixed(4)}`;
            Civic.toast('Coordinates set','ok',2000);
          })
          .finally(()=>{
            useLocationBtn.disabled=false;
            useLocationBtn.textContent='Use Current Location';
          });
      },
      (error)=>{
        console.error('Geolocation error:',error);
        Civic.toast(`Location error: ${error.message}`,'err',3000);
        useLocationBtn.disabled=false;
        useLocationBtn.textContent='Use Current Location';
      },
      {enableHighAccuracy:true,timeout:10000,maximumAge:0}
    );
  });
}


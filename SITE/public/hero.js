(function(){
  var r=document.getElementById('cmr'); if(!r) return;
  var reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var seen=false; try{seen=sessionStorage.getItem('cmr-filled')==='1';}catch(e){}
  if(!reduced&&!seen){ r.classList.add('fill'); try{sessionStorage.setItem('cmr-filled','1');}catch(e){} }
})();

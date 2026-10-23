(function(){function r(){if(!window.katex)return;
document.querySelectorAll('.tx:not(.r)').forEach(function(el){try{katex.render(el.textContent,el,
{displayMode:el.dataset.d==='1',throwOnError:false,strict:'ignore'})}catch(e){}el.classList.add('r')})}
if(document.readyState!=='loading')r();else document.addEventListener('DOMContentLoaded',r)})();

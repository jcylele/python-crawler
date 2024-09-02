import{S as et,P as ot}from"./Consts-cfe4b018.js";import{E as rt,h as y,u as x,v as F,_ as st,o as C,c as T,w as u,r as h,b as l,f as nt,g as at,F as it,d as U,t as lt}from"./index-1be7bb4c.js";import{B as ct,D as ut}from"./DownloadCtrl-fd0b6de6.js";import{L as _t,P as ft}from"./Enums-58228667.js";class I{get show_category(){return this.show_rows[0]}set show_category(t){this.show_rows[0]=t,this.resetCategory()}get show_tag(){return this.show_rows[1]}set show_tag(t){this.show_rows[1]=t,this.resetTags()}get show_score(){return this.show_rows[2]}set show_score(t){this.show_rows[2]=t,this.resetScores()}get show_name(){return this.show_rows[3]}set show_name(t){this.show_rows[3]=t,this.resetName()}get show_sort(){return this.show_rows[4]}set show_sort(t){this.show_rows[4]=t,this.resetSort()}get show_remark(){return this.show_rows[5]}set show_remark(t){this.show_rows[5]=t,this.resetRemark()}get show_min_score(){return this.min_score/2}set show_min_score(t){this.min_score=t*2}get show_max_score(){return this.max_score/2}set show_max_score(t){this.max_score=t*2}get show_sort_id(){return this.sort_id}set show_sort_id(t){this.sort_id=t;for(const o of et)if(o.id==t){this.sort_type=o.sort_type,this.sort_asc=o.sort_asc;return}}constructor(){this.show_rows=new Array(6).fill(!1),this.all_category_list=[],this.reset()}reset(){this.resetCategory(),this.resetTags(),this.resetScores(),this.resetName(),this.resetSort(),this.resetRemark()}clone(){const t=new I;return t.copy(this),t}copy(t){this.show_rows=t.show_rows.slice(),this.name=t.name,this.category_list=t.category_list.slice(),this.tag_list=t.tag_list.slice(),this.no_tag=t.no_tag,this.min_score=t.min_score,this.max_score=t.max_score,this.show_sort_id=t.show_sort_id,this.remark_str=t.remark_str,this.remark_any=t.remark_any}setAllCategoryList(t){this.all_category_list=t}resetCategory(){this.checkAllCategory(!0)}checkAllCategory(t){t?this.category_list=this.all_category_list.slice():this.category_list=[]}resetTags(){this.tag_list=[],this.no_tag=!1}onCheckedTagChange(){this.tag_list.length>0&&(this.no_tag=!1)}checkNoTag(t){t&&(this.tag_list=[])}resetScores(){this.min_score=0,this.max_score=10}onFilterNameChange(){}resetName(){this.name=""}resetSort(){this.show_sort_id=0}resetRemark(){this.remark_str="",this.remark_any=!1}checkAnyRemark(t){t&&(this.remark_str="")}}const N="3.7.5",dt=N,ht=typeof atob=="function",mt=typeof btoa=="function",g=typeof Buffer=="function",z=typeof TextDecoder=="function"?new TextDecoder:void 0,P=typeof TextEncoder=="function"?new TextEncoder:void 0,wt="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",p=Array.prototype.slice.call(wt),A=(e=>{let t={};return e.forEach((o,r)=>t[o]=r),t})(p),gt=/^(?:[A-Za-z\d+\/]{4})*?(?:[A-Za-z\d+\/]{2}(?:==)?|[A-Za-z\d+\/]{3}=?)?$/,c=String.fromCharCode.bind(String),R=typeof Uint8Array.from=="function"?Uint8Array.from.bind(Uint8Array):e=>new Uint8Array(Array.prototype.slice.call(e,0)),j=e=>e.replace(/=/g,"").replace(/[+\/]/g,t=>t=="+"?"-":"_"),O=e=>e.replace(/[^A-Za-z0-9\+\/]/g,""),Z=e=>{let t,o,r,s,n="";const a=e.length%3;for(let _=0;_<e.length;){if((o=e.charCodeAt(_++))>255||(r=e.charCodeAt(_++))>255||(s=e.charCodeAt(_++))>255)throw new TypeError("invalid character found");t=o<<16|r<<8|s,n+=p[t>>18&63]+p[t>>12&63]+p[t>>6&63]+p[t&63]}return a?n.slice(0,a-3)+"===".substring(a):n},v=mt?e=>btoa(e):g?e=>Buffer.from(e,"binary").toString("base64"):Z,V=g?e=>Buffer.from(e).toString("base64"):e=>{let o=[];for(let r=0,s=e.length;r<s;r+=4096)o.push(c.apply(null,e.subarray(r,r+4096)));return v(o.join(""))},k=(e,t=!1)=>t?j(V(e)):V(e),pt=e=>{if(e.length<2){var t=e.charCodeAt(0);return t<128?e:t<2048?c(192|t>>>6)+c(128|t&63):c(224|t>>>12&15)+c(128|t>>>6&63)+c(128|t&63)}else{var t=65536+(e.charCodeAt(0)-55296)*1024+(e.charCodeAt(1)-56320);return c(240|t>>>18&7)+c(128|t>>>12&63)+c(128|t>>>6&63)+c(128|t&63)}},yt=/[\uD800-\uDBFF][\uDC00-\uDFFFF]|[^\x00-\x7F]/g,M=e=>e.replace(yt,pt),E=g?e=>Buffer.from(e,"utf8").toString("base64"):P?e=>V(P.encode(e)):e=>v(M(e)),w=(e,t=!1)=>t?j(E(e)):E(e),L=e=>w(e,!0),xt=/[\xC0-\xDF][\x80-\xBF]|[\xE0-\xEF][\x80-\xBF]{2}|[\xF0-\xF7][\x80-\xBF]{3}/g,bt=e=>{switch(e.length){case 4:var t=(7&e.charCodeAt(0))<<18|(63&e.charCodeAt(1))<<12|(63&e.charCodeAt(2))<<6|63&e.charCodeAt(3),o=t-65536;return c((o>>>10)+55296)+c((o&1023)+56320);case 3:return c((15&e.charCodeAt(0))<<12|(63&e.charCodeAt(1))<<6|63&e.charCodeAt(2));default:return c((31&e.charCodeAt(0))<<6|63&e.charCodeAt(1))}},G=e=>e.replace(xt,bt),q=e=>{if(e=e.replace(/\s+/g,""),!gt.test(e))throw new TypeError("malformed base64.");e+="==".slice(2-(e.length&3));let t,o="",r,s;for(let n=0;n<e.length;)t=A[e.charAt(n++)]<<18|A[e.charAt(n++)]<<12|(r=A[e.charAt(n++)])<<6|(s=A[e.charAt(n++)]),o+=r===64?c(t>>16&255):s===64?c(t>>16&255,t>>8&255):c(t>>16&255,t>>8&255,t&255);return o},S=ht?e=>atob(O(e)):g?e=>Buffer.from(e,"base64").toString("binary"):q,H=g?e=>R(Buffer.from(e,"base64")):e=>R(S(e).split("").map(t=>t.charCodeAt(0))),J=e=>H(K(e)),At=g?e=>Buffer.from(e,"base64").toString("utf8"):z?e=>z.decode(H(e)):e=>G(S(e)),K=e=>O(e.replace(/[-_]/g,t=>t=="-"?"+":"/")),B=e=>At(K(e)),kt=e=>{if(typeof e!="string")return!1;const t=e.replace(/\s+/g,"").replace(/={0,2}$/,"");return!/[^\s0-9a-zA-Z\+/]/.test(t)||!/[^\s0-9a-zA-Z\-_]/.test(t)},Q=e=>({value:e,enumerable:!1,writable:!0,configurable:!0}),W=function(){const e=(t,o)=>Object.defineProperty(String.prototype,t,Q(o));e("fromBase64",function(){return B(this)}),e("toBase64",function(t){return w(this,t)}),e("toBase64URI",function(){return w(this,!0)}),e("toBase64URL",function(){return w(this,!0)}),e("toUint8Array",function(){return J(this)})},X=function(){const e=(t,o)=>Object.defineProperty(Uint8Array.prototype,t,Q(o));e("toBase64",function(t){return k(this,t)}),e("toBase64URI",function(){return k(this,!0)}),e("toBase64URL",function(){return k(this,!0)})},Ct=()=>{W(),X()},Y={version:N,VERSION:dt,atob:S,atobPolyfill:q,btoa:v,btoaPolyfill:Z,fromBase64:B,toBase64:w,encode:w,encodeURI:L,encodeURL:L,utob:M,btou:G,decode:B,isValid:kt,fromUint8Array:k,toUint8Array:J,extendString:W,extendUint8Array:X,extendBuiltins:Ct},Ut=["未下载","已下载","大文件","已删除"];class d extends rt{constructor(t){super(t),t.remark?this.remark=Y.decode(t.remark):this.remark=""}get post_desc(){return this.file_info.unfinished_post_count>0?`[${this.file_info.finished_post_count}(+${this.file_info.unfinished_post_count})/${this.file_info.total_post_count}]`:`[${this.file_info.finished_post_count}/${this.file_info.total_post_count}]`}get show_score(){return this.score/2}set show_score(t){this.score=t*2}sortTags(t){this.tag_ids.sort(t)}hasTag(t){return this.tag_ids.indexOf(t)>=0}formatResFileInfo(t){let o=t.res_size/1073741824;return o=Math.floor(o*100)/100,`${Ut[t.res_state-1]}: ${o}G(${t.img_count}P,${t.video_count}V)`}get icon(){return`http://localhost:1314/_icon/${this.actor_name}.jfif`}get remark_list(){return this.remark!=null&&this.remark!=""?this.remark.split(`
`):[]}}const f="http://127.0.0.1:8000/api/actor";async function Dt(e){const t=`${f}/count`,[o,r]=await y(t,e);return o?[!0,r.value]:[o,r]}async function Tt(e,t=0,o=0){const r=`${f}/list?limit=${t}&start=${o}`,[s,n]=await y(r,e);if(!s)return[s,n];const a=[];for(const _ of n)a.push(new d(_));return[!0,a]}async function zt(e,t){let o=`${f}/${e}/tag?`;const r=[];for(const _ of t)r.push(`id=${_}`);o+=r.join("&");const[s,n]=await y(o);return s?[!0,new d(n)]:[!1,n]}async function Pt(e){const t=`${f}/${e}/open`;return await x(t)}async function Rt(e){const t=`${f}/${e}/clear`;return await x(t)}async function Et(e){const t=`${f}/${e}/reset_posts`;return await x(t)}async function Lt(e,t){const o=`${f}/${e}/category?val=${t}`,[r,s]=await F(o);return r?[!0,new d(s)]:[!1,s]}async function It(e,t){const o=`${f}/batch/category`;let r=new ct;r.category=t,r.actor_names=e;const[s,n]=await y(o,r);if(!s)return[!1,n];const a=[];for(const _ of n)a.push(new d(_));return[!0,a]}async function Nt(e,t){const o=`${f}/${e}/score?val=${t}`,[r,s]=await F(o);return r?[!0,new d(s)]:[!1,s]}async function jt(e,t){const o=Y.encodeURI(t),r=`${f}/${e}/remark?val=${o}`,[s,n]=await F(r);return s?[!0,new d(n)]:[!1,n]}async function Ot(e){const t=`${f}/${e}/file_info`,[o,r]=await x(t);return o?[!0,r]:[!1,r]}async function Zt(e){const t=`${f}/link`,[o,r]=await y(t,e);if(!o)return[!1,r];const s={};for(const n of r){const a=new d(n);s[a.actor_name]=a}return[!0,s]}async function Mt(e){const t=`${f}/${e}/link`,[o,r]=await x(t);if(!o)return[!1,r];const s=[];for(const n of r)s.push(new d(n));return[!0,s]}const Vt={name:"DownloadLimit",props:{download_limit:ut},data(){return{cur_preset:_t.All,post_filter:ft}},computed:{preset_option_list(){return ot}},watch:{async cur_preset(e,t){this.download_limit.resetDefaultValue(e)}}};function Bt(e,t,o,r,s,n){const a=h("el-radio"),_=h("el-radio-group"),$=h("el-space"),b=h("el-input-number"),m=h("el-form-item"),D=h("el-checkbox"),tt=h("el-form");return C(),T($,{direction:"vertical",class:"limit-form"},{default:u(()=>[l($,{direction:"horizontal",wrap:""},{default:u(()=>[l(_,{modelValue:s.cur_preset,"onUpdate:modelValue":t[0]||(t[0]=i=>s.cur_preset=i)},{default:u(()=>[(C(!0),nt(it,null,at(n.preset_option_list,i=>(C(),T(a,{value:i.value},{default:u(()=>[U(lt(i.label),1)]),_:2},1032,["value"]))),256))]),_:1},8,["modelValue"])]),_:1}),l(tt,{model:o.download_limit,"label-width":"200px","label-position":"left"},{default:u(()=>[l(m,{label:"Actor Count"},{default:u(()=>[l(b,{modelValue:o.download_limit.actor_count,"onUpdate:modelValue":t[1]||(t[1]=i=>o.download_limit.actor_count=i),min:0,max:200,step:5},null,8,["modelValue"])]),_:1}),l(m,{label:"Post Filter"},{default:u(()=>[l(_,{modelValue:o.download_limit.post_filter,"onUpdate:modelValue":t[2]||(t[2]=i=>o.download_limit.post_filter=i)},{default:u(()=>[l(a,{value:s.post_filter.Normal},{default:u(()=>[U("Normal")]),_:1},8,["value"]),l(a,{value:s.post_filter.Old},{default:u(()=>[U("Current")]),_:1},8,["value"])]),_:1},8,["modelValue"])]),_:1}),l(m,{label:"Post Count"},{default:u(()=>[l(b,{modelValue:o.download_limit.post_count,"onUpdate:modelValue":t[3]||(t[3]=i=>o.download_limit.post_count=i),min:0,max:9999,step:50},null,8,["modelValue"])]),_:1}),l(m,{label:"Total File Size(MB)"},{default:u(()=>[l(b,{modelValue:o.download_limit.show_total_file_size,"onUpdate:modelValue":t[4]||(t[4]=i=>o.download_limit.show_total_file_size=i),min:0,max:10240,step:512},null,8,["modelValue"])]),_:1}),l(m,{label:"Single File Size(MB)"},{default:u(()=>[l(b,{modelValue:o.download_limit.show_file_size,"onUpdate:modelValue":t[5]||(t[5]=i=>o.download_limit.show_file_size=i),min:0,max:1024,step:20},null,8,["modelValue"])]),_:1}),l(m,{label:"File Types"},{default:u(()=>[l(D,{modelValue:o.download_limit.allow_img,"onUpdate:modelValue":t[6]||(t[6]=i=>o.download_limit.allow_img=i),label:"Images",size:"large"},null,8,["modelValue"]),l(D,{modelValue:o.download_limit.allow_video,"onUpdate:modelValue":t[7]||(t[7]=i=>o.download_limit.allow_video=i),label:"Videos",size:"large"},null,8,["modelValue"])]),_:1})]),_:1},8,["model"])]),_:1})}const Gt=st(Vt,[["render",Bt],["__scopeId","data-v-9b70f242"]]);export{I as A,zt as C,Gt as D,d as a,Lt as b,Rt as c,Nt as d,jt as e,Tt as f,Ot as g,Dt as h,Mt as i,It as j,Zt as l,Pt as o,Et as r};

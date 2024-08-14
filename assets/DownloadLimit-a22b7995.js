import{S as et,P as ot}from"./Consts-b58d017b.js";import{E as st,h as x,u as B,v as F,_ as rt,o as k,c as z,w as u,r as h,b as i,f as nt,g as at,F as it,d as b,t as lt}from"./index-172ad7fb.js";import{B as ct,D as ut}from"./DownloadCtrl-5af7ecc1.js";import{L as _t,P as ft}from"./Enums-e33e938b.js";class N{get show_category(){return this.show_rows[0]}set show_category(t){this.show_rows[0]=t,this.resetCategory()}get show_tag(){return this.show_rows[1]}set show_tag(t){this.show_rows[1]=t,this.resetTags()}get show_score(){return this.show_rows[2]}set show_score(t){this.show_rows[2]=t,this.resetScores()}get show_name(){return this.show_rows[3]}set show_name(t){this.show_rows[3]=t,this.resetName()}get show_sort(){return this.show_rows[4]}set show_sort(t){this.show_rows[4]=t,this.resetSort()}get show_remark(){return this.show_rows[5]}set show_remark(t){this.show_rows[5]=t,this.resetRemark()}get show_min_score(){return this.min_score/2}set show_min_score(t){this.min_score=t*2}get show_max_score(){return this.max_score/2}set show_max_score(t){this.max_score=t*2}get show_sort_id(){return this.sort_id}set show_sort_id(t){this.sort_id=t;for(const o of et)if(o.id==t){this.sort_type=o.sort_type,this.sort_asc=o.sort_asc;return}}constructor(){this.show_rows=new Array(6).fill(!1),this.all_category_list=[],this.reset()}reset(){this.resetCategory(),this.resetTags(),this.resetScores(),this.resetName(),this.resetSort(),this.resetRemark()}clone(){const t=new N;return t.show_rows=this.show_rows.slice(),t.name=this.name,t.category_list=this.category_list.slice(),t.tag_list=this.tag_list.slice(),t.no_tag=this.no_tag,t.min_score=this.min_score,t.max_score=this.max_score,t.show_sort_id=this.show_sort_id,t}copy(t){this.show_rows=t.show_rows.slice(),this.name=t.name,this.category_list=t.category_list.slice(),this.tag_list=t.tag_list.slice(),this.no_tag=t.no_tag,this.min_score=t.min_score,this.max_score=t.max_score,this.show_sort_id=t.show_sort_id}setAllCategoryList(t){this.all_category_list=t}resetCategory(){this.checkAllCategory(!0)}checkAllCategory(t){t?this.category_list=this.all_category_list.slice():this.category_list=[]}resetTags(){this.tag_list=[],this.no_tag=!1}onCheckedTagChange(){this.tag_list.length>0&&(this.no_tag=!1)}checkNoTag(t){t&&(this.tag_list=[])}resetScores(){this.min_score=0,this.max_score=10}onFilterNameChange(){}resetName(){this.name=""}resetSort(){this.show_sort_id=0}resetRemark(){this.remark_str="",this.remark_any=!1}}const I="3.7.5",dt=I,ht=typeof atob=="function",mt=typeof btoa=="function",g=typeof Buffer=="function",P=typeof TextDecoder=="function"?new TextDecoder:void 0,R=typeof TextEncoder=="function"?new TextEncoder:void 0,wt="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",p=Array.prototype.slice.call(wt),A=(e=>{let t={};return e.forEach((o,s)=>t[o]=s),t})(p),gt=/^(?:[A-Za-z\d+\/]{4})*?(?:[A-Za-z\d+\/]{2}(?:==)?|[A-Za-z\d+\/]{3}=?)?$/,c=String.fromCharCode.bind(String),$=typeof Uint8Array.from=="function"?Uint8Array.from.bind(Uint8Array):e=>new Uint8Array(Array.prototype.slice.call(e,0)),O=e=>e.replace(/=/g,"").replace(/[+\/]/g,t=>t=="+"?"-":"_"),j=e=>e.replace(/[^A-Za-z0-9\+\/]/g,""),Z=e=>{let t,o,s,r,n="";const a=e.length%3;for(let _=0;_<e.length;){if((o=e.charCodeAt(_++))>255||(s=e.charCodeAt(_++))>255||(r=e.charCodeAt(_++))>255)throw new TypeError("invalid character found");t=o<<16|s<<8|r,n+=p[t>>18&63]+p[t>>12&63]+p[t>>6&63]+p[t&63]}return a?n.slice(0,a-3)+"===".substring(a):n},S=mt?e=>btoa(e):g?e=>Buffer.from(e,"binary").toString("base64"):Z,U=g?e=>Buffer.from(e).toString("base64"):e=>{let o=[];for(let s=0,r=e.length;s<r;s+=4096)o.push(c.apply(null,e.subarray(s,s+4096)));return S(o.join(""))},C=(e,t=!1)=>t?O(U(e)):U(e),pt=e=>{if(e.length<2){var t=e.charCodeAt(0);return t<128?e:t<2048?c(192|t>>>6)+c(128|t&63):c(224|t>>>12&15)+c(128|t>>>6&63)+c(128|t&63)}else{var t=65536+(e.charCodeAt(0)-55296)*1024+(e.charCodeAt(1)-56320);return c(240|t>>>18&7)+c(128|t>>>12&63)+c(128|t>>>6&63)+c(128|t&63)}},xt=/[\uD800-\uDBFF][\uDC00-\uDFFFF]|[^\x00-\x7F]/g,M=e=>e.replace(xt,pt),E=g?e=>Buffer.from(e,"utf8").toString("base64"):R?e=>U(R.encode(e)):e=>S(M(e)),w=(e,t=!1)=>t?O(E(e)):E(e),L=e=>w(e,!0),yt=/[\xC0-\xDF][\x80-\xBF]|[\xE0-\xEF][\x80-\xBF]{2}|[\xF0-\xF7][\x80-\xBF]{3}/g,bt=e=>{switch(e.length){case 4:var t=(7&e.charCodeAt(0))<<18|(63&e.charCodeAt(1))<<12|(63&e.charCodeAt(2))<<6|63&e.charCodeAt(3),o=t-65536;return c((o>>>10)+55296)+c((o&1023)+56320);case 3:return c((15&e.charCodeAt(0))<<12|(63&e.charCodeAt(1))<<6|63&e.charCodeAt(2));default:return c((31&e.charCodeAt(0))<<6|63&e.charCodeAt(1))}},G=e=>e.replace(yt,bt),q=e=>{if(e=e.replace(/\s+/g,""),!gt.test(e))throw new TypeError("malformed base64.");e+="==".slice(2-(e.length&3));let t,o="",s,r;for(let n=0;n<e.length;)t=A[e.charAt(n++)]<<18|A[e.charAt(n++)]<<12|(s=A[e.charAt(n++)])<<6|(r=A[e.charAt(n++)]),o+=s===64?c(t>>16&255):r===64?c(t>>16&255,t>>8&255):c(t>>16&255,t>>8&255,t&255);return o},D=ht?e=>atob(j(e)):g?e=>Buffer.from(e,"base64").toString("binary"):q,H=g?e=>$(Buffer.from(e,"base64")):e=>$(D(e).split("").map(t=>t.charCodeAt(0))),J=e=>H(K(e)),At=g?e=>Buffer.from(e,"base64").toString("utf8"):P?e=>P.decode(H(e)):e=>G(D(e)),K=e=>j(e.replace(/[-_]/g,t=>t=="-"?"+":"/")),V=e=>At(K(e)),Ct=e=>{if(typeof e!="string")return!1;const t=e.replace(/\s+/g,"").replace(/={0,2}$/,"");return!/[^\s0-9a-zA-Z\+/]/.test(t)||!/[^\s0-9a-zA-Z\-_]/.test(t)},Q=e=>({value:e,enumerable:!1,writable:!0,configurable:!0}),W=function(){const e=(t,o)=>Object.defineProperty(String.prototype,t,Q(o));e("fromBase64",function(){return V(this)}),e("toBase64",function(t){return w(this,t)}),e("toBase64URI",function(){return w(this,!0)}),e("toBase64URL",function(){return w(this,!0)}),e("toUint8Array",function(){return J(this)})},X=function(){const e=(t,o)=>Object.defineProperty(Uint8Array.prototype,t,Q(o));e("toBase64",function(t){return C(this,t)}),e("toBase64URI",function(){return C(this,!0)}),e("toBase64URL",function(){return C(this,!0)})},kt=()=>{W(),X()},Y={version:I,VERSION:dt,atob:D,atobPolyfill:q,btoa:S,btoaPolyfill:Z,fromBase64:V,toBase64:w,encode:w,encodeURI:L,encodeURL:L,utob:M,btou:G,decode:V,isValid:Ct,fromUint8Array:C,toUint8Array:J,extendString:W,extendUint8Array:X,extendBuiltins:kt},Ut=["未下载","已下载","大文件","已删除"];class d extends st{constructor(t){super(t),t.remark&&(this.remark=Y.decode(t.remark))}get post_desc(){let t=`[${this.finished_post_count}`;return this.unfinished_post_count>0&&(t+=`(+${this.unfinished_post_count})`),t+=`/${this.total_post_count}]`,t}get show_score(){return this.score/2}set show_score(t){this.score=t*2}sortTags(t){this.rel_tags.sort(t)}hasTag(t){return this.rel_tags.indexOf(t)>=0}formatResFileInfo(t){let o=t.res_size/1073741824;return o=Math.floor(o*100)/100,`${Ut[t.res_state-1]}: ${o}G(${t.img_count}P,${t.video_count}V)`}get icon(){return`http://localhost:1314/_icon/${this.actor_name}.jfif`}get remark_list(){return this.remark!=null&&this.remark!=""?this.remark.split(`
`):[]}}const f="http://127.0.0.1:8000/api/actor";async function Tt(e){const t=`${f}/count`,[o,s]=await x(t,e);return o?[!0,s.value]:[o,s]}async function zt(e,t=0,o=0){const s=`${f}/list?limit=${t}&start=${o}`,[r,n]=await x(s,e);if(!r)return[r,n];const a=[];for(const _ of n)a.push(new d(_));return[!0,a]}async function Pt(e,t){let o=`${f}/${e}/tag?`;const s=[];for(const _ of t)s.push(`id=${_}`);o+=s.join("&");const[r,n]=await x(o);return r?[!0,new d(n)]:[!1,n]}async function Rt(e){const t=`${f}/${e}/open`;return await B(t)}async function $t(e,t){const o=`${f}/${e}/category?val=${t}`,[s,r]=await F(o);return s?[!0,new d(r)]:[!1,r]}async function Et(e,t){const o=`${f}/batch/category`;let s=new ct;s.category=t,s.actor_names=e;const[r,n]=await x(o,s);if(!r)return[!1,n];const a=[];for(const _ of n)a.push(new d(_));return[!0,a]}async function Lt(e,t){const o=`${f}/${e}/score?val=${t}`,[s,r]=await F(o);return s?[!0,new d(r)]:[!1,r]}async function Nt(e,t){const o=Y.encodeURI(t),s=`${f}/${e}/remark?val=${o}`,[r,n]=await F(s);return r?[!0,new d(n)]:[!1,n]}async function It(e){const t=`${f}/${e}/file_info`,[o,s]=await B(t);return o?[!0,s]:[!1,s]}async function Ot(e){const t=`${f}/link`,[o,s]=await x(t,e);if(!o)return[!1,s];const r={};for(const n of s){const a=new d(n);r[a.actor_name]=a}return[!0,r]}async function jt(e){const t=`${f}/${e}/link`,[o,s]=await B(t);if(!o)return[!1,s];const r=[];for(const n of s)r.push(new d(n));return[!0,r]}const Vt={name:"DownloadLimit",props:{download_limit:ut},data(){return{cur_preset:_t.All,post_filter:ft}},computed:{preset_option_list(){return ot}},watch:{async cur_preset(e,t){this.download_limit.resetDefaultValue(e)}}};function Bt(e,t,o,s,r,n){const a=h("el-radio"),_=h("el-radio-group"),v=h("el-space"),y=h("el-input-number"),m=h("el-form-item"),T=h("el-checkbox"),tt=h("el-form");return k(),z(v,{direction:"vertical",class:"limit-form"},{default:u(()=>[i(v,{direction:"horizontal",wrap:""},{default:u(()=>[i(_,{modelValue:r.cur_preset,"onUpdate:modelValue":t[0]||(t[0]=l=>r.cur_preset=l)},{default:u(()=>[(k(!0),nt(it,null,at(n.preset_option_list,l=>(k(),z(a,{label:l.value},{default:u(()=>[b(lt(l.label),1)]),_:2},1032,["label"]))),256))]),_:1},8,["modelValue"])]),_:1}),i(tt,{model:o.download_limit,"label-width":"200px","label-position":"left"},{default:u(()=>[i(m,{label:"Actor Count"},{default:u(()=>[i(y,{modelValue:o.download_limit.actor_count,"onUpdate:modelValue":t[1]||(t[1]=l=>o.download_limit.actor_count=l),max:200,step:5},null,8,["modelValue"])]),_:1}),i(m,{label:"Post Filter"},{default:u(()=>[i(_,{modelValue:o.download_limit.post_filter,"onUpdate:modelValue":t[2]||(t[2]=l=>o.download_limit.post_filter=l)},{default:u(()=>[i(a,{label:r.post_filter.Normal},{default:u(()=>[b("Normal")]),_:1},8,["label"]),i(a,{label:r.post_filter.Old},{default:u(()=>[b("Current")]),_:1},8,["label"]),i(a,{label:r.post_filter.New},{default:u(()=>[b("New")]),_:1},8,["label"])]),_:1},8,["modelValue"])]),_:1}),i(m,{label:"Post Count"},{default:u(()=>[i(y,{modelValue:o.download_limit.post_count,"onUpdate:modelValue":t[3]||(t[3]=l=>o.download_limit.post_count=l),max:9999,step:50},null,8,["modelValue"])]),_:1}),i(m,{label:"Total File Size(MB)"},{default:u(()=>[i(y,{modelValue:o.download_limit.show_total_file_size,"onUpdate:modelValue":t[4]||(t[4]=l=>o.download_limit.show_total_file_size=l),max:10240,step:512},null,8,["modelValue"])]),_:1}),i(m,{label:"Single File Size(MB)"},{default:u(()=>[i(y,{modelValue:o.download_limit.show_file_size,"onUpdate:modelValue":t[5]||(t[5]=l=>o.download_limit.show_file_size=l),max:1024,step:20},null,8,["modelValue"])]),_:1}),i(m,{label:"File Types"},{default:u(()=>[i(T,{modelValue:o.download_limit.allow_img,"onUpdate:modelValue":t[6]||(t[6]=l=>o.download_limit.allow_img=l),label:"Images",size:"large"},null,8,["modelValue"]),i(T,{modelValue:o.download_limit.allow_video,"onUpdate:modelValue":t[7]||(t[7]=l=>o.download_limit.allow_video=l),label:"Videos",size:"large"},null,8,["modelValue"])]),_:1})]),_:1},8,["model"])]),_:1})}const Zt=rt(Vt,[["render",Bt],["__scopeId","data-v-090e4a25"]]);export{N as A,Pt as C,Zt as D,d as a,Lt as b,$t as c,Nt as d,zt as e,Tt as f,It as g,jt as h,Et as i,Ot as l,Rt as o};

import{E as p,h as c,u as h,x as w}from"./index-1be7bb4c.js";import{P as i,L as l}from"./Enums-58228667.js";class m{}class D extends m{}class B{}class d{}class y extends d{}class u extends d{}class z extends u{}class _{constructor(t){Object.assign(this,t)}get show_file_size(){return this.file_size/(1024*1024)}set show_file_size(t){this.file_size=t*(1024*1024)}get show_total_file_size(){return this.total_file_size/(1024*1024)}set show_total_file_size(t){this.total_file_size=t*(1024*1024)}format_file_size(t){return t>=1024*1024*1024?`${t/(1024*1024*1024)} GB`:t>=1024*1024?`${t/(1024*1024)} MB`:t>=1024?`${t/1024} KB`:`${t} B`}file_size_desc(){return this.format_file_size(this.file_size)}total_file_size_desc(){return this.format_file_size(this.total_file_size)}resetDefaultValue(t){switch(console.log(`preset_val: ${t}`),this.actor_count=0,this.post_count=0,this.show_file_size=0,this.show_total_file_size=0,this.allow_video=!0,this.allow_img=!0,this.post_filter=i.Normal,t){case l.All:break;case l.Init:this.actor_count=50,this.post_count=50,this.show_file_size=20,this.show_total_file_size=1024;break;case l.Current_Init:this.post_filter=i.Old,this.show_file_size=20,this.show_total_file_size=1024;break;case l.Current_Video:this.post_filter=i.Old,this.allow_img=!1;break;case l.Only_Info:this.show_file_size=1,this.show_total_file_size=1}}static NewForm(t){const e=new _;return e.resetDefaultValue(t),e}setPageLimit(t){t<1?this.post_count=0:this.post_count=t*50}post_desc(){switch(console.log(`${this.post_filter}-${this.post_count}`),this.post_filter){case i.Old:return"current posts";case i.New:return"latest posts";default:return this.post_count==0?"all posts":`${this.post_count} posts`}}}class $ extends p{constructor(t){super(t),this.download_limit=new _(t.download_limit)}}const n="http://127.0.0.1:8000/api/download";async function F(s,t){let e=`${n}/specific`;const o=new y;o.download_limit=s,o.actor_names=t;const[r,a]=await c(e,o);return r?[!0,a.value]:[r,a]}async function b(s,t,e){let o=`${n}/urls`;const r=new z;r.actor_category=s,r.download_limit=t,r.urls=e;const[a,f]=await c(o,r);return a?[!0,f.value]:[a,f]}async function A(s,t){const e=`${n}/new`,o=new u;o.actor_category=s,o.download_limit=t;const[r,a]=await c(e,o);return r?[!0,a.value]:[r,a]}async function v(s,t){const e=`${n}/category`,o=new u;o.actor_category=s,o.download_limit=t;const[r,a]=await c(e,o);return r?[!0,a.value]:[r,a]}async function x(){const s=`${n}/list`,[t,e]=await h(s);if(!t)return[t,e];const o=[];for(const r of e)o.push(new $(r));return[!0,o]}async function N(s){const t=`${n}/${s}`,[e,o]=await w(t);return e?[!0,o.value]:[e,o]}async function O(){const s=`${n}/all`,[t,e]=await w(s);return t?[!0,e.value]:[t,e]}async function C(){const s=`${n}/clean`,[t,e]=await h(s);return[t,e]}export{B as A,D as B,_ as D,b as a,v as b,A as c,F as d,O as e,C as f,x as g,N as s};
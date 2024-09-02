import{A as q,a as ie,o as re,c as se,r as ce,b as _e,C as Z,d as de,e as $,g as ue,D as me,f as ge,h as he,i as fe,l as pe,j as ke}from"./DownloadLimit-0cce0427.js";import{N as ee}from"./NewActorTag-940c86cb.js";import{m as D,A as G,a as L,_ as I,o as r,c as d,w as n,r as i,b as a,d as _,e as k,f as x,g as v,F as b,t as z,n as M,E as ye,h as O,l as H,i as W,j as U,k as N,p as E,q as te,s as we}from"./index-1be7bb4c.js";import{S as Ce,a as X,A as xe}from"./Consts-cfe4b018.js";import{D as be,d as Ae}from"./DownloadCtrl-fd0b6de6.js";import{A as B,L as ve}from"./Enums-58228667.js";const Ve={name:"ActorFilter",props:{filter_condition:q},emits:["change","submit"],components:{NewActorTag:ee},data(){return{is_category_all:!1,filter_history:[]}},computed:{...D(G,{actor_tag_list:"sorted_list"}),...D(L,{actor_group_list:"sorted_list"}),sort_option_list(){return Ce},star_colors(){return X}},watch:{async is_category_all(t,e){t&&this.fillAllCategory(),this.filter_condition.checkAllCategory(t)}},methods:{onAnyConditionChange(){this.$emit("change")},checkNoTag(t){this.onAnyConditionChange(),this.filter_condition.checkNoTag(t)},onCheckedTagChange(){this.onAnyConditionChange(),this.filter_condition.onCheckedTagChange()},onCheckedCategoryChange(t){},checkAnyRemark(t){this.onAnyConditionChange(),this.filter_condition.checkAnyRemark(t)},async onFilterSubmit(){this.filter_history.push(this.filter_condition.clone()),this.$emit("submit")},onFilterCancel(){this.filter_condition.reset(),this.$emit("change")},async toPreviousFilter(){this.filter_history.length>0&&this.filter_condition.copy(this.filter_history.pop())},fillAllCategory(){this.filter_condition.setAllCategoryList(this.actor_group_list.map(t=>t.group_id))}},mounted(){}};function ze(t,e,l,C,c,o){const f=i("el-checkbox"),A=i("el-divider"),g=i("el-button"),m=i("el-space"),y=i("el-checkbox-button"),h=i("el-checkbox-group"),V=i("el-switch"),w=i("el-form-item"),S=i("el-option"),F=i("el-select"),u=i("el-rate"),T=i("el-text"),P=i("el-input"),R=i("el-form");return r(),d(m,{direction:"vertical",fill:!0},{default:n(()=>[a(m,{direction:"horizontal",alignment:"flex-start",class:"filter"},{default:n(()=>[a(f,{size:"large",border:"",modelValue:l.filter_condition.show_category,"onUpdate:modelValue":e[0]||(e[0]=s=>l.filter_condition.show_category=s)},{default:n(()=>[_("Category")]),_:1},8,["modelValue"]),a(f,{size:"large",border:"",modelValue:l.filter_condition.show_tag,"onUpdate:modelValue":e[1]||(e[1]=s=>l.filter_condition.show_tag=s)},{default:n(()=>[_("Tag")]),_:1},8,["modelValue"]),a(f,{size:"large",border:"",modelValue:l.filter_condition.show_score,"onUpdate:modelValue":e[2]||(e[2]=s=>l.filter_condition.show_score=s)},{default:n(()=>[_("Star")]),_:1},8,["modelValue"]),a(f,{size:"large",border:"",modelValue:l.filter_condition.show_name,"onUpdate:modelValue":e[3]||(e[3]=s=>l.filter_condition.show_name=s)},{default:n(()=>[_("Name")]),_:1},8,["modelValue"]),a(f,{size:"large",border:"",modelValue:l.filter_condition.show_remark,"onUpdate:modelValue":e[4]||(e[4]=s=>l.filter_condition.show_remark=s)},{default:n(()=>[_("Remark")]),_:1},8,["modelValue"]),a(f,{size:"large",border:"",modelValue:l.filter_condition.show_sort,"onUpdate:modelValue":e[5]||(e[5]=s=>l.filter_condition.show_sort=s)},{default:n(()=>[_("Sort")]),_:1},8,["modelValue"]),a(A,{direction:"vertical"}),a(g,{type:"primary",size:"large",onClick:o.onFilterSubmit},{default:n(()=>[_("Search")]),_:1},8,["onClick"]),a(g,{type:"warning",size:"large",onClick:o.onFilterCancel},{default:n(()=>[_("Reset")]),_:1},8,["onClick"]),c.filter_history.length>0?(r(),d(g,{key:0,type:"success",size:"large",onClick:o.toPreviousFilter},{default:n(()=>[_("Previous ")]),_:1},8,["onClick"])):k("",!0)]),_:1}),a(R,{model:l.filter_condition,"label-width":"auto","label-position":"right",class:"filter-form"},{default:n(()=>[l.filter_condition.show_category?(r(),d(w,{key:0,label:"Category"},{default:n(()=>[a(h,{modelValue:l.filter_condition.category_list,"onUpdate:modelValue":e[6]||(e[6]=s=>l.filter_condition.category_list=s),onChange:o.onAnyConditionChange,size:"default"},{default:n(()=>[(r(!0),x(b,null,v(t.actor_group_list,s=>(r(),d(y,{value:s.group_id},{default:n(()=>[_(z(s.group_name),1)]),_:2},1032,["value"]))),256))]),_:1},8,["modelValue","onChange"]),a(V,{modelValue:c.is_category_all,"onUpdate:modelValue":e[7]||(e[7]=s=>c.is_category_all=s),size:"large","active-text":"All","inactive-text":"None",style:{"margin-left":"10px"}},null,8,["modelValue"])]),_:1})):k("",!0),l.filter_condition.show_tag?(r(),d(w,{key:1,label:"Tags"},{default:n(()=>[a(F,{modelValue:l.filter_condition.tag_list,"onUpdate:modelValue":e[8]||(e[8]=s=>l.filter_condition.tag_list=s),onChange:o.onCheckedTagChange,style:{width:"200px"},size:"default",multiple:"",filterable:"",clearable:""},{default:n(()=>[(r(!0),x(b,null,v(t.actor_tag_list,s=>(r(),d(S,{key:s.tag_id,label:s.tag_name,value:s.tag_id},null,8,["label","value"]))),128))]),_:1},8,["modelValue","onChange"]),a(f,{modelValue:l.filter_condition.no_tag,"onUpdate:modelValue":e[9]||(e[9]=s=>l.filter_condition.no_tag=s),onChange:o.checkNoTag,style:{"margin-left":"10px","font-size":"24px"},size:"default",border:""},{default:n(()=>[_(" No Tag ")]),_:1},8,["modelValue","onChange"])]),_:1})):k("",!0),l.filter_condition.show_score?(r(),d(w,{key:2,label:"Star"},{default:n(()=>[a(u,{modelValue:l.filter_condition.show_min_score,"onUpdate:modelValue":e[10]||(e[10]=s=>l.filter_condition.show_min_score=s),onChange:o.onAnyConditionChange,colors:o.star_colors,"void-color":"#777777",size:"large","allow-half":""},null,8,["modelValue","onChange","colors"]),a(T,null,{default:n(()=>[_("~")]),_:1}),a(u,{modelValue:l.filter_condition.show_max_score,"onUpdate:modelValue":e[11]||(e[11]=s=>l.filter_condition.show_max_score=s),onChange:o.onAnyConditionChange,colors:o.star_colors,"void-color":"#777777",size:"large","allow-half":""},null,8,["modelValue","onChange","colors"])]),_:1})):k("",!0),l.filter_condition.show_name?(r(),d(w,{key:3,label:"Name"},{default:n(()=>[a(P,{modelValue:l.filter_condition.name,"onUpdate:modelValue":e[12]||(e[12]=s=>l.filter_condition.name=s),onChange:o.onAnyConditionChange,style:{width:"200px","font-size":"24px","margin-right":"20px"},clearable:""},null,8,["modelValue","onChange"])]),_:1})):k("",!0),l.filter_condition.show_remark?(r(),d(w,{key:4,label:"Remark"},{default:n(()=>[a(P,{modelValue:l.filter_condition.remark_str,"onUpdate:modelValue":e[13]||(e[13]=s=>l.filter_condition.remark_str=s),onChange:o.onAnyConditionChange,style:{width:"200px","font-size":"24px"},clearable:""},null,8,["modelValue","onChange"]),a(f,{modelValue:l.filter_condition.remark_any,"onUpdate:modelValue":e[14]||(e[14]=s=>l.filter_condition.remark_any=s),onChange:o.checkAnyRemark,style:{"margin-left":"10px","font-size":"24px"},border:""},{default:n(()=>[_(" Any Remark ")]),_:1},8,["modelValue","onChange"])]),_:1})):k("",!0),l.filter_condition.show_sort?(r(),d(w,{key:5,label:"Sort"},{default:n(()=>[a(F,{modelValue:l.filter_condition.show_sort_id,"onUpdate:modelValue":e[15]||(e[15]=s=>l.filter_condition.show_sort_id=s),onChange:o.onAnyConditionChange,style:{width:"200px"}},{default:n(()=>[(r(!0),x(b,null,v(o.sort_option_list,s=>(r(),d(S,{label:s.label,value:s.id},null,8,["label","value"]))),256))]),_:1},8,["modelValue","onChange"])]),_:1})):k("",!0)]),_:1},8,["model"])]),_:1})}const Se=I(Ve,[["render",ze],["__scopeId","data-v-4020ea24"]]),Fe={name:"ActorTagChooser",props:{actor:ie},emits:["submit","cancel"],components:{NewActorTag:ee},data(){return{search_text:"",editing_tags:[]}},computed:{...D(G,{actor_tag_list:"sorted_list"})},mounted(){console.log(`mounted ActorTagChooser for [${this.actor.actor_name}]`),this.initTags()},methods:{onSearchTextChange(){console.log("onSearchTextChange",this.search_text)},searchClass(t){return this.search_text==""?"normal-text":t.tag.tag_name.includes(this.search_text)?"filtered-text":"failed-text"},initTags(){this.editing_tags=[];for(let t=0;t<10;t++)this.editing_tags.push([]);for(const t of this.actor_tag_list){const e=Math.floor(t.tag_priority/100),l=this.actor.hasTag(t.tag_id);this.editing_tags[e].push({tag:t,selected:l})}this.editing_tags.reverse()},onSubmit(){let t=[];for(const e of this.editing_tags)for(const l of e)l.selected&&t.push(l.tag.tag_id);this.editing_tags=[],this.$emit("submit",t)},onCancel(){this.$emit("cancel")}}};function Te(t,e,l,C,c,o){const f=i("NewActorTag"),A=i("el-input"),g=i("el-checkbox-button"),m=i("el-space"),y=i("el-button"),h=i("el-container");return r(),d(h,null,{default:n(()=>[a(m,{direction:"vertical",size:"default",fill:!0},{default:n(()=>[a(f,{onTag_added:o.initTags},null,8,["onTag_added"]),a(A,{modelValue:c.search_text,"onUpdate:modelValue":e[0]||(e[0]=V=>c.search_text=V),onInput:o.onSearchTextChange,placeholder:"Search tags",clearable:""},null,8,["modelValue","onInput"]),(r(!0),x(b,null,v(c.editing_tags,V=>(r(),d(m,{style:{border:"1px solid","border-radius":"4px",padding:"2px"},direction:"horizontal",wrap:!0,size:3,alignment:"stretch"},{default:n(()=>[(r(!0),x(b,null,v(V,w=>(r(),d(g,{modelValue:w.selected,"onUpdate:modelValue":S=>w.selected=S,style:{margin:"3px"},class:M(o.searchClass(w))},{default:n(()=>[_(z(w.tag.tag_name),1)]),_:2},1032,["modelValue","onUpdate:modelValue","class"]))),256))]),_:2},1024))),256)),a(m,{direction:"horizontal",alignment:"center"},{default:n(()=>[a(y,{type:"primary",onClick:o.onSubmit},{default:n(()=>[_(" Save ")]),_:1},8,["onClick"]),a(y,{type:"warning",onClick:o.onCancel},{default:n(()=>[_(" Cancel ")]),_:1},8,["onClick"])]),_:1})]),_:1})]),_:1})}const oe=I(Fe,[["render",Te],["__scopeId","data-v-2e5e36f9"]]),Pe={name:"RemarkEditor",props:{remark:{type:String,required:!0}},data(){return{remark_items:[]}},methods:{onClear(t){this.remark_items.splice(t,1)},onAddRemark(){this.remark_items.push({data:""})},onSubmit(){if(this.remark_items.length==0){this.$emit("submit","");return}const t=this.remark_items.map(e=>e.data).join(`
`);this.$emit("submit",t)},onCancel(){this.$emit("cancel")}},mounted(){if(this.remark_items=[],this.remark!=null&&this.remark!=""){let t=this.remark.split(`
`);for(let e=0;e<t.length;e++)this.remark_items.push({data:t[e]})}}};function Ue(t,e,l,C,c,o){const f=i("el-text"),A=i("svg-icon"),g=i("el-space"),m=i("el-input"),y=i("el-button");return r(),d(g,{direction:"vertical",fill:!0},{default:n(()=>[a(g,{direction:"horizontal"},{default:n(()=>[a(f,{style:{"font-size":"24px",color:"hotpink"}},{default:n(()=>[_(" Remarks ")]),_:1}),a(A,{size:"24px",name:"add",onClick:o.onAddRemark},null,8,["onClick"])]),_:1}),(r(!0),x(b,null,v(c.remark_items,(h,V)=>(r(),d(g,{direction:"horizontal",alignment:"center"},{default:n(()=>[a(m,{modelValue:h.data,"onUpdate:modelValue":w=>h.data=w,style:{width:"500px"}},null,8,["modelValue","onUpdate:modelValue"]),a(A,{name:"remove",size:"24px",onClick:w=>o.onClear(V)},null,8,["onClick"])]),_:2},1024))),256)),a(g,{direction:"horizontal",alignment:"stretch"},{default:n(()=>[a(y,{type:"primary",onClick:o.onSubmit},{default:n(()=>[_(" Save ")]),_:1},8,["onClick"]),a(y,{type:"warning",onClick:o.onCancel},{default:n(()=>[_(" Cancel ")]),_:1},8,["onClick"])]),_:1})]),_:1})}const ne=I(Pe,[["render",Ue]]);class Q{get is_editing(){return this._is_editing}set is_editing(e){if(this._is_editing!=e){if(e)this.actor_name=this.fixed_actor_name||"";else if(this.post_id_prefix.length<this.calcMinPrefixLength())return;this._is_editing=e}}get has_actor_name(){return this.actor_name!=""}calcMinPrefixLength(){return this.has_comment?0:this.actor_name.length>0?3:5}constructor(e){this.fixed_actor_name=e,this.actor_name=e||"",this.post_id_prefix="",this.has_comment=!1,this._is_editing=!0}}class Ie{}class De extends ye{}const J="http://127.0.0.1:8000/api/post";async function Le(t){const e=`${J}/actor_list`;return await O(e,t)}async function Re(t){const e=`${J}/post_list`,[l,C]=await O(e,t);if(!l)return[l,C];const c=[];for(const o of C){const f=new De(o);c.push(f)}return[!0,c]}async function Ne(t,e){const l=`${J}/set_comment`,C=new Ie;return C.post_id=t,C.comment=e,await O(l,C)}const Ee={name:"Posts",props:{specific_actor_name:{type:String,required:!1}},data(){return{conditionForm:Q,actor_post_list:[],post_list:[]}},methods:{startEdit(){this.conditionForm.is_editing=!0,this.actor_post_list=[],this.post_list=[]},endEdit(){if(this.conditionForm.is_editing=!1,this.conditionForm.is_editing){let t=this.conditionForm.calcMinPrefixLength();H(`prefix of post id should be at least ${t} bits`);return}this.conditionForm.actor_name!==""?this.getActorPosts():this.getActorNames()},async getActorNames(){const[t,e]=await Le(this.conditionForm);t&&(this.actor_post_list=e,this.post_list=[])},async getActorPosts(){const[t,e]=await Re(this.conditionForm);t&&(this.post_list=e)},async onPostEdit(t){if(t.is_editing){const[e,l]=await Ne(t.post_id,t.comment);e&&(t.is_editing=!1)}else t.is_editing=!0}},mounted(){console.log(`posts of ${this.specific_actor_name}`),this.conditionForm=new Q(this.specific_actor_name)}};function Ge(t,e,l,C,c,o){const f=i("el-input"),A=i("el-checkbox"),g=i("el-button"),m=i("el-space"),y=i("el-divider"),h=i("el-badge"),V=i("el-radio"),w=i("el-radio-group"),S=i("el-text"),F=i("svg-icon");return r(),d(m,{direction:"vertical",fill:!0,style:{"padding-bottom":"5px"}},{default:n(()=>[a(m,{direction:"horizontal",size:"small"},{default:n(()=>[c.conditionForm.has_actor_name?(r(),d(f,{key:0,disabled:""},{default:n(()=>[_(z(c.conditionForm.actor_name),1)]),_:1})):k("",!0),a(f,{modelValue:c.conditionForm.post_id_prefix,"onUpdate:modelValue":e[0]||(e[0]=u=>c.conditionForm.post_id_prefix=u),placeholder:"Post Id Prefix",clearable:"",disabled:!c.conditionForm.is_editing,style:{width:"150px"}},null,8,["modelValue","disabled"]),a(A,{modelValue:c.conditionForm.has_comment,"onUpdate:modelValue":e[1]||(e[1]=u=>c.conditionForm.has_comment=u),disabled:!c.conditionForm.is_editing,style:{"font-size":"20px"},size:"default",border:""},{default:n(()=>[_(" Has Comment ")]),_:1},8,["modelValue","disabled"]),c.conditionForm.is_editing?k("",!0):(r(),d(g,{key:1,type:"success",onClick:o.startEdit},{default:n(()=>[_("Edit")]),_:1},8,["onClick"])),c.conditionForm.is_editing?(r(),d(g,{key:2,type:"primary",onClick:o.endEdit},{default:n(()=>[_("Save")]),_:1},8,["onClick"])):k("",!0)]),_:1}),l.specific_actor_name?k("",!0):(r(),d(y,{key:0,style:{margin:"5px 0"}})),l.specific_actor_name?k("",!0):(r(),d(m,{key:1,direction:"horizontal",wrap:""},{default:n(()=>[a(w,{modelValue:c.conditionForm.actor_name,"onUpdate:modelValue":e[2]||(e[2]=u=>c.conditionForm.actor_name=u),onChange:o.getActorPosts},{default:n(()=>[(r(!0),x(b,null,v(c.actor_post_list,u=>(r(),d(V,{value:u.actor_name},{default:n(()=>[_(z(u.actor_name)+" ",1),a(h,{class:"mark",value:u.post_count},null,8,["value"])]),_:2},1032,["value"]))),256))]),_:1},8,["modelValue","onChange"])]),_:1})),a(y,{style:{margin:"5px 0"}}),(r(!0),x(b,null,v(c.post_list,u=>(r(),d(m,{direction:"horizontal"},{default:n(()=>[a(S,{style:{"font-size":"22px",color:"royalblue"}},{default:n(()=>[_(z(u.post_id),1)]),_:2},1024),a(F,{onClick:T=>o.onPostEdit(u),size:"24px",name:u.is_editing?"check":"edit"},null,8,["onClick","name"]),u.is_editing?(r(),d(f,{key:0,modelValue:u.comment,"onUpdate:modelValue":T=>u.comment=T,placeholder:"add comment for post",clearable:"",style:{width:"300px","font-size":"20px"}},null,8,["modelValue","onUpdate:modelValue"])):k("",!0),u.is_editing?k("",!0):(r(),d(S,{key:1,style:{"font-size":"20px"}},{default:n(()=>[_(z(u.comment),1)]),_:2},1024))]),_:2},1024))),256))]),_:1})}const ae=I(Ee,[["render",Ge]]);class K{constructor(e){this.data=e}set data(e){this.actor=e}get data(){return this.actor}get id(){return this.actor.uuid}}function j(t){const e=[];for(const l of t)e.push(new K(l));return e}const Me={name:"ActorCard",components:{ActorTagChooser:oe,SvgIcon:W,RemarkEditor:ne,Posts:ae},props:{actor_data:K,show_link:Boolean},computed:{...D(L,{group_list:"sorted_list"}),actor(){return this.actor_data.data},star_colors(){return X},group_color(){return this.getActorGroup(this.actor_data.data.actor_category).group_color}},emits:["refresh","link","download","friend"],data(){return{is_editing_tags:!1,is_show_post:!1,is_show_op:!1}},mounted(){this.actor.sortTags(this.compareActorTagId),this.getFileInfo()},methods:{...U(G,{compareActorTagId:"compareTagId",getTagStyleName:"getStyleName",getTagName:"getName"}),...U(L,{getActorGroup:"get"}),getActorGroupData(){let t=this.actor_data.data.actor_category;return this.getActorGroup(t)},hasFolder(){return this.getActorGroupData().has_folder},onRecvActorMsg(t,e,l){t&&(this.actor_data.data=e,this.actor.sortTags(this.compareActorTagId),this.$emit("refresh",this.actor_data),N(l),this.getFileInfo())},gotoActorPage(){this.is_show_op=!1,window.open(this.actor.href,"_blank","noreferrer")},openFolder(){this.is_show_op=!1,re(this.actor.actor_name)},async clearFolder(){this.is_show_op=!1;const[t,e]=await se(this.actor.actor_name);t&&(this.setFileInfo(e),N("clear folder succeed"))},async resetPosts(){this.is_show_op=!1;const[t,e]=await ce(this.actor.actor_name);t&&(this.setFileInfo(e),N("reset posts succeed"))},async setActorCategory(){if(this.actor.tag_ids.length==0){H("add any tag before setting category");return}const[t,e]=await _e(this.actor.actor_name,this.actor.actor_category);this.onRecvActorMsg(t,e,"change category succeed")},onStartEditTag(){this.is_editing_tags=!0},async onSubmitTag(t){this.is_editing_tags=!1;const[e,l]=await Z(this.actor.actor_name,t);this.onRecvActorMsg(e,l,"change tags succeed")},async onCancelAddTag(){this.is_editing_tags=!1},toDownload(){this.is_show_op=!1,this.$emit("download",this.actor_data)},showPosts(){this.is_show_op=!1,this.is_show_post=!0},async changeScore(){const[t,e]=await de(this.actor.actor_name,this.actor.score);this.onRecvActorMsg(t,e,"change score succeed")},async findLinkedActor(){this.$emit("friend",this.actor_data)},onLinkClick(){this.$emit("link",this.actor_data)},async onSubmitRemark(t){if(t==this.actor.remark)return;const[e,l]=await $(this.actor.actor_name,t);this.onRecvActorMsg(e,l,"change remark succeed")},async getFileInfo(){const[t,e]=await ue(this.actor.actor_name);t&&this.setFileInfo(e)},setFileInfo(t){this.actor.file_info=t}}};const Be={class:"avatar"};function je(t,e,l,C,c,o){const f=i("el-image"),A=i("svg-icon"),g=i("el-rate"),m=i("el-text"),y=i("el-button"),h=i("el-space"),V=i("el-popover"),w=i("RemarkEditor"),S=i("el-option"),F=i("el-select"),u=i("el-tag"),T=i("ActorTagChooser"),P=i("el-dialog"),R=i("Posts");return r(),x(b,null,[(r(),d(h,{direction:"vertical",class:"actor_card",alignment:"stretch",size:3,key:o.actor.uuid,style:E({color:o.group_color})},{default:n(()=>[te("div",Be,[a(f,{class:"avatar-img",src:o.actor.icon},null,8,["src"]),o.actor.has_main_actor?(r(),d(A,{key:0,size:"30px",name:"friend",style:{position:"absolute",top:"0",left:"15px"},onClick:o.findLinkedActor},null,8,["onClick"])):k("",!0),l.show_link?(r(),d(A,{key:1,size:"30px",name:"top",style:{position:"absolute",top:"0",right:"15px"},class:"blink-class",onClick:o.onLinkClick},null,8,["onClick"])):k("",!0),a(g,{class:"avatar-rate",modelValue:o.actor.show_score,"onUpdate:modelValue":e[0]||(e[0]=s=>o.actor.show_score=s),colors:o.star_colors,"void-color":"#777777",size:"large",onChange:o.changeScore,"allow-half":""},null,8,["modelValue","colors","onChange"])]),a(V,{trigger:"click",placement:"top",visible:c.is_show_op,"onUpdate:visible":e[1]||(e[1]=s=>c.is_show_op=s),"popper-style":{"border-color":o.group_color,width:300},"popper-class":"op_popper",offset:6},{reference:n(()=>[a(m,{class:"actor_name",style:E({color:o.group_color})},{default:n(()=>[_(z(o.actor.actor_name),1)]),_:1},8,["style"])]),default:n(()=>[a(h,{direction:"vertical",alignment:"center"},{default:n(()=>[a(h,{direction:"horizontal"},{default:n(()=>[a(y,{class:"pop-button",type:"primary",onClick:o.showPosts},{default:n(()=>[_(" Show Posts ")]),_:1},8,["onClick"]),a(y,{class:"pop-button",type:"primary",onClick:o.gotoActorPage},{default:n(()=>[_(" Go To Page ")]),_:1},8,["onClick"])]),_:1}),o.hasFolder()?(r(),d(h,{key:0,direction:"horizontal"},{default:n(()=>[a(y,{class:"pop-button",type:"warning",onClick:o.resetPosts},{default:n(()=>[_(" Reset Posts ")]),_:1},8,["onClick"]),a(y,{class:"pop-button",type:"warning",onClick:o.clearFolder},{default:n(()=>[_(" Clear Folder ")]),_:1},8,["onClick"])]),_:1})):k("",!0),o.hasFolder()?(r(),d(h,{key:1,direction:"horizontal"},{default:n(()=>[o.hasFolder()?(r(),d(y,{key:0,class:"pop-button",type:"success",onClick:o.toDownload},{default:n(()=>[_(" Download ")]),_:1},8,["onClick"])):k("",!0),o.hasFolder()?(r(),d(y,{key:1,class:"pop-button",type:"success",onClick:o.openFolder},{default:n(()=>[_(" Open Folder ")]),_:1},8,["onClick"])):k("",!0)]),_:1})):k("",!0)]),_:1})]),_:1},8,["visible","popper-style"]),o.actor.file_info?(r(),d(h,{key:0,direction:"vertical",alignment:"start",style:{gap:"1px 0px","padding-left":"15px"}},{default:n(()=>[a(m,{style:{"font-size":"18px",color:"black"},tag:"ins"},{default:n(()=>[_(z(o.actor.post_desc),1)]),_:1}),(r(!0),x(b,null,v(o.actor.file_info.res_info,s=>(r(),d(m,{class:M("res"+s.res_state),style:{"font-size":"14px"}},{default:n(()=>[_(z(o.actor.formatResFileInfo(s)),1)]),_:2},1032,["class"]))),256))]),_:1})):k("",!0),a(h,{direction:"horizontal",alignment:"stretch"},{default:n(()=>[a(V,{placement:"right",trigger:"click",width:600},{reference:n(()=>[a(A,{size:"24px",name:o.actor.remark?"remark":"remark_empty"},null,8,["name"])]),default:n(()=>[a(w,{remark:o.actor.remark,onSubmit:o.onSubmitRemark},null,8,["remark","onSubmit"])]),_:1}),a(F,{modelValue:o.actor.actor_category,"onUpdate:modelValue":e[2]||(e[2]=s=>o.actor.actor_category=s),onChange:o.setActorCategory,style:{width:"140px"}},{default:n(()=>[(r(!0),x(b,null,v(t.group_list,s=>(r(),d(S,{label:s.group_name,value:s.group_id,style:E({color:s.group_color,"text-decoration":"underline"})},{default:n(()=>[_(z(s.show_content),1)]),_:2},1032,["label","value","style"]))),256))]),_:1},8,["modelValue","onChange"]),a(A,{onClick:e[3]||(e[3]=s=>o.onStartEditTag()),size:"24px",name:"edit"})]),_:1}),a(h,{wrap:"",style:{"margin-top":"5px"}},{default:n(()=>[(r(!0),x(b,null,v(o.actor.tag_ids,s=>(r(),d(u,{class:M(t.getTagStyleName(s)),style:{"font-size":"18px"},round:""},{default:n(()=>[_(z(t.getTagName(s)),1)]),_:2},1032,["class"]))),256))]),_:1})]),_:1},8,["style"])),a(P,{modelValue:c.is_editing_tags,"onUpdate:modelValue":e[4]||(e[4]=s=>c.is_editing_tags=s),title:o.actor.actor_name,width:"67%"},{default:n(()=>[a(T,{actor:o.actor,onSubmit:o.onSubmitTag,onCancel:o.onCancelAddTag},null,8,["actor","onSubmit","onCancel"])]),_:1},8,["modelValue","title"]),a(P,{modelValue:c.is_show_post,"onUpdate:modelValue":e[5]||(e[5]=s=>c.is_show_post=s),title:"Posts",width:"720px"},{default:n(()=>[a(R,{specific_actor_name:o.actor.actor_name},null,8,["specific_actor_name"])]),_:1},8,["modelValue"])],64)}const qe=I(Me,[["render",je],["__scopeId","data-v-e362156d"]]),Y=we("ActorFilterStore",{state:()=>({filter:null,page_info:{page_size:12,page_index:1}}),getters:{filter_condition:t=>(t.filter===null&&(t.filter=new q),t.filter),page_size:t=>t.page_info.page_size,page_index:t=>t.page_info.page_index},actions:{setFilter(t){this.filter=t.clone()},setPageIndex(t){this.page_info.page_index=t},setPageSize(t){this.page_info.page_size=t}}}),Oe={name:"ActorLine",components:{SvgIcon:W,RemarkEditor:ne,ActorTagChooser:oe},props:{actor_data:K},computed:{actor(){return this.actor_data.data},star_colors(){return X}},data(){return{is_editing_tags:!1}},methods:{...U(L,{getActorGroup:"get"}),...U(G,{compareActorTagId:"compareTagId",getTagStyleName:"getStyleName",getTagName:"getName"}),getGroupColor(t){return this.getActorGroup(t).group_color},async onSubmitRemark(t){if(t==this.actor.remark)return;const[e,l]=await $(this.actor.actor_name,t);this.onRecvActorMsg(e,l,"change remark succeed")},onStartEditTag(){this.is_editing_tags=!0},async onSubmitTag(t){this.is_editing_tags=!1;const[e,l]=await Z(this.actor.actor_name,t);this.onRecvActorMsg(e,l,"change tags succeed")},async onCancelAddTag(){this.is_editing_tags=!1},onRecvActorMsg(t,e,l){t&&(this.actor_data.data=e,this.actor.sortTags(this.compareActorTagId),N(l))}},mounted(){this.actor.sortTags(this.compareActorTagId)}};const He={style:{position:"relative",margin:"10px",height:"100px",width:"100px"}};function We(t,e,l,C,c,o){const f=i("el-image"),A=i("el-rate"),g=i("el-text"),m=i("svg-icon"),y=i("el-tag"),h=i("el-space"),V=i("RemarkEditor"),w=i("el-popover"),S=i("ActorTagChooser"),F=i("el-dialog");return r(),x(b,null,[(r(),d(h,{direction:"horizontal",size:"large",class:"actor_line",alignment:"center",key:o.actor.uuid,shadow:"always",style:E({color:o.getGroupColor(o.actor.actor_category)})},{default:n(()=>[te("div",He,[a(f,{src:o.actor.icon},null,8,["src"]),a(A,{modelValue:o.actor.show_score,"onUpdate:modelValue":e[0]||(e[0]=u=>o.actor.show_score=u),colors:o.star_colors,"void-color":"#777777",size:"small",style:{position:"absolute",bottom:"0",left:"50%",transform:"translateX(-50%)"},"allow-half":"",disabled:""},null,8,["modelValue","colors"])]),a(h,{direction:"vertical",alignment:"start",size:"small"},{default:n(()=>[a(g,{class:"actor_name"},{default:n(()=>[_(z(o.actor.actor_name),1)]),_:1}),a(h,{direction:"horizontal",wrap:""},{default:n(()=>[a(m,{onClick:o.onStartEditTag,size:"24px",name:"edit"},null,8,["onClick"]),(r(!0),x(b,null,v(o.actor.tag_ids,u=>(r(),d(y,{class:M(t.getTagStyleName(u)),style:{"font-size":"18px"},round:""},{default:n(()=>[_(z(t.getTagName(u)),1)]),_:2},1032,["class"]))),256))]),_:1}),a(h,{direction:"horizontal",alignment:"start"},{default:n(()=>[a(w,{placement:"right",trigger:"click",width:600},{reference:n(()=>[a(m,{size:"24px",name:o.actor.remark?"remark":"remark_empty"},null,8,["name"])]),default:n(()=>[a(V,{remark:o.actor.remark,onSubmit:o.onSubmitRemark},null,8,["remark","onSubmit"])]),_:1}),a(h,{direction:"vertical",alignment:"start"},{default:n(()=>[(r(!0),x(b,null,v(o.actor.remark_list,u=>(r(),d(g,{onClick:e[1]||(e[1]=()=>{})},{default:n(()=>[_(z(u),1)]),_:2},1024))),256))]),_:1})]),_:1})]),_:1})]),_:1},8,["style"])),a(F,{modelValue:c.is_editing_tags,"onUpdate:modelValue":e[2]||(e[2]=u=>c.is_editing_tags=u),title:o.actor.actor_name,width:"67%"},{default:n(()=>[a(S,{actor:o.actor,onSubmit:o.onSubmitTag,onCancel:o.onCancelAddTag},null,8,["actor","onSubmit","onCancel"])]),_:1},8,["modelValue","title"])],64)}const Xe=I(Oe,[["render",We],["__scopeId","data-v-f4b3f114"]]),Je={components:{SvgIcon:W,Posts:ae,ActorLine:Xe,ActorCard:qe,ActorFilter:Se,DownloadLimit:me},data(){return{filter_condition:new q,actor_list:[],page_size:12,page_index:1,actor_count:0,active_parts:["filter"],linked_list:[],download_actor_names:[],download_limit:null,actor_show_type:B.Card,is_show_post:!1}},computed:{...D(Y,{cached_filter_condition:"filter_condition",cached_page_size:"page_size",cached_page_index:"page_index"}),...D(L,{group_list:"sorted_list"}),show_link(){return this.active_parts.includes("link")},is_show_download(){return this.download_actor_names.length>0},download_title(){switch(this.download_actor_names.length){case 0:return"";case 1:return this.download_actor_names[0];default:{let e=this.download_actor_names.join(",");return e.length>30&&(e=e.substring(0,30),e+="..."),e}}},actor_show_options(){return xe},actor_show_card(){return this.actor_show_type==B.Card},actor_show_line(){return this.actor_show_type==B.Line}},methods:{...U(G,{getTagsFromServer:"getFromServer"}),...U(Y,{saveFilterCondition:"setFilter",savePageIndex:"setPageIndex",savePageSize:"setPageSize"}),...U(L,{getGroupsFromServer:"getFromServer"}),async handleSizeChange(t){this.page_size=t,this.savePageSize(t),this.page_index=1,await this.onActorPageChange()},async onActorPageChange(){this.savePageIndex(this.page_index);const[t,e]=await ge(this.filter_condition,this.page_size,(this.page_index-1)*this.page_size);t?this.actor_list=j(e):this.actor_list=[]},onFilterChange(){this.savePageIndex(1),this.page_index=1,this.actor_list=[],this.actor_count=0},async onFilterSubmit(){this.saveFilterCondition(this.filter_condition),this.actor_list=[],this.actor_count=0;const[t,e]=await he(this.filter_condition);t&&(this.actor_count=e,this.refreshPageIndex(),await this.onActorPageChange())},refreshPageIndex(){let t=Math.ceil(this.actor_count/this.page_size);this.page_index=this.cached_page_index,this.page_index>t&&(this.page_index=t),this.page_index<1&&(this.page_index=1)},onActorChange(t){console.log(`actor changed: ${t.data.actor_name}`)},async onActorFriendClick(t){console.log(`actor friend clicked: ${t.data.actor_name}`);const[e,l]=await fe(t.data.actor_name);e?this.actor_list=j(l):this.actor_list=[]},async onActorLinkClick(t){this.linked_list.push(t)},async linkActors(){if(this.linked_list.length<2){H("No actor to link");return}const t=this.linked_list.map(C=>C.data.actor_name),[e,l]=await pe(t);if(e)for(const C of this.linked_list)C.data.actor_name in l&&(C.data=l[C.data.actor_name]);else this.linked_list=[]},clearLinkedActors(){this.linked_list=[]},showDownloadLimit(t){this.download_actor_names=t,this.download_limit==null&&(this.download_limit=new be,this.download_limit.resetDefaultValue(ve.Current_Init))},singleShowDownload(t){this.showDownloadLimit([t.data.actor_name])},batchShowDownload(){let t=this.actor_list.map(e=>e.data.actor_name);this.showDownloadLimit(t)},async onSubmitDownload(){let[t,e]=await Ae(this.download_limit,this.download_actor_names);this.onDownloadClose(),t&&N("download started")},onDownloadClose(){this.download_actor_names=[]},async batchSetActorCategory(t){let e=this.actor_list.map(c=>c.data.actor_name),[l,C]=await ke(e,t);l?this.actor_list=j(C):this.actor_list=[]},showPosts(){this.is_show_post=!0},onActivePartChange(){this.show_link||(this.linked_list=[])}},watch:{},async mounted(){this.filter_condition=this.cached_filter_condition,this.page_size=this.cached_page_size,this.page_index=this.cached_page_index,await this.getTagsFromServer(),await this.getGroupsFromServer()}};function Ke(t,e,l,C,c,o){const f=i("el-text"),A=i("svg-icon"),g=i("el-button"),m=i("el-space"),y=i("ActorCard"),h=i("el-collapse-item"),V=i("ActorFilter"),w=i("el-collapse"),S=i("el-pagination"),F=i("el-option"),u=i("el-select"),T=i("el-popover"),P=i("ActorLine"),R=i("DownloadLimit"),s=i("el-dialog"),le=i("Posts");return r(),x(b,null,[a(m,{direction:"vertical",fill:!0},{default:n(()=>[a(w,{modelValue:c.active_parts,"onUpdate:modelValue":e[0]||(e[0]=p=>c.active_parts=p),onChange:o.onActivePartChange},{default:n(()=>[a(h,{name:"link",title:""},{title:n(()=>[a(f,{style:{"font-size":"24px","font-style":"oblique","margin-right":"10px"}},{default:n(()=>[_(" Link Actors ")]),_:1}),a(A,{size:"24px",name:"link"})]),default:n(()=>[a(m,{direction:"horizontal"},{default:n(()=>[a(m,{direction:"vertical",alignment:"stretch"},{default:n(()=>[a(g,{type:"primary",size:"large",onClick:o.linkActors},{default:n(()=>[_("Link")]),_:1},8,["onClick"]),a(g,{type:"warning",size:"large",onClick:o.clearLinkedActors},{default:n(()=>[_("Clear")]),_:1},8,["onClick"])]),_:1}),o.actor_show_card?(r(),d(m,{key:0,direction:"horizontal",class:"card_row",alignment:"stretch"},{default:n(()=>[(r(!0),x(b,null,v(c.linked_list,p=>(r(),d(y,{actor_data:p,show_link:!1,key:p.id},null,8,["actor_data"]))),128))]),_:1})):k("",!0)]),_:1})]),_:1}),a(h,{name:"filter"},{title:n(()=>[a(f,{style:{"font-size":"24px","font-style":"oblique","margin-right":"10px"}},{default:n(()=>[_(" Actor Filter ")]),_:1}),a(A,{size:"24px",name:"filter"})]),default:n(()=>[a(m,{direction:"vertical"},{default:n(()=>[a(V,{filter_condition:c.filter_condition,onChange:o.onFilterChange,onSubmit:o.onFilterSubmit},null,8,["filter_condition","onChange","onSubmit"])]),_:1})]),_:1})]),_:1},8,["modelValue","onChange"]),a(m,{direction:"horizontal",size:"large",spacer:"|"},{default:n(()=>[a(S,{"current-page":c.page_index,"onUpdate:currentPage":e[1]||(e[1]=p=>c.page_index=p),"page-size":c.page_size,"page-sizes":[12,14],total:c.actor_count,onCurrentChange:o.onActorPageChange,onSizeChange:o.handleSizeChange,layout:"sizes, total, prev, pager, next",background:"",style:{margin:"5px"}},null,8,["current-page","page-size","total","onCurrentChange","onSizeChange"]),a(T,{trigger:"click",placement:"right",width:"200px"},{reference:n(()=>[a(g,null,{default:n(()=>[_("Operate These Actors")]),_:1})]),default:n(()=>[a(m,{direction:"vertical",style:{width:"180px"},fill:!0},{default:n(()=>[a(g,{onClick:o.batchShowDownload},{default:n(()=>[_(" Batch Download ")]),_:1},8,["onClick"]),a(u,{placeholder:"Batch Set Category",onChange:o.batchSetActorCategory},{default:n(()=>[(r(!0),x(b,null,v(t.group_list,p=>(r(),d(F,{label:p.show_content,value:p.group_id,style:E({color:p.group_color})},null,8,["label","value","style"]))),256))]),_:1},8,["onChange"])]),_:1})]),_:1}),a(u,{modelValue:c.actor_show_type,"onUpdate:modelValue":e[2]||(e[2]=p=>c.actor_show_type=p),style:{"min-width":"100px"}},{default:n(()=>[(r(!0),x(b,null,v(o.actor_show_options,p=>(r(),d(F,{label:p.label,value:p.value},null,8,["label","value"]))),256))]),_:1},8,["modelValue"]),a(g,{type:"primary",onClick:o.showPosts},{default:n(()=>[_(" Posts ")]),_:1},8,["onClick"])]),_:1}),o.actor_show_card?(r(),d(m,{key:0,direction:"horizontal",class:"card_row",alignment:"stretch",style:{gap:"15px 15px"}},{default:n(()=>[(r(!0),x(b,null,v(c.actor_list,p=>(r(),d(y,{actor_data:p,show_link:o.show_link,key:p.id,onRefresh:o.onActorChange,onFriend:o.onActorFriendClick,onLink:o.onActorLinkClick,onDownload:o.singleShowDownload},null,8,["actor_data","show_link","onRefresh","onFriend","onLink","onDownload"]))),128))]),_:1})):k("",!0),o.actor_show_line?(r(),d(m,{key:1,direction:"vertical",size:"small",fill:!0},{default:n(()=>[(r(!0),x(b,null,v(c.actor_list,p=>(r(),d(P,{actor_data:p,key:p.id},null,8,["actor_data"]))),128))]),_:1})):k("",!0)]),_:1}),a(s,{modelValue:o.is_show_download,"onUpdate:modelValue":e[3]||(e[3]=p=>o.is_show_download=p),title:o.download_title,"before-close":o.onDownloadClose,width:"640px"},{default:n(()=>[a(m,{direction:"vertical"},{default:n(()=>[a(R,{download_limit:c.download_limit},null,8,["download_limit"]),a(m,{direction:"horizontal",alignment:"center"},{default:n(()=>[a(g,{type:"primary",onClick:o.onSubmitDownload},{default:n(()=>[_(" Download ")]),_:1},8,["onClick"]),a(g,{type:"warning",onClick:o.onDownloadClose},{default:n(()=>[_(" Cancel ")]),_:1},8,["onClick"])]),_:1})]),_:1})]),_:1},8,["modelValue","title","before-close"]),a(s,{modelValue:c.is_show_post,"onUpdate:modelValue":e[4]||(e[4]=p=>c.is_show_post=p),title:"Posts",width:"720px"},{default:n(()=>[a(le)]),_:1},8,["modelValue"])],64)}const ot=I(Je,[["render",Ke],["__scopeId","data-v-b8faa5fe"]]);export{ot as default};
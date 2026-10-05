package com.androidcompiler.mobile;
import android.app.*;import android.content.*;import android.net.Uri;import android.os.*;import android.provider.DocumentsContract;
import org.json.*;import java.io.*;import java.net.*;import java.nio.file.*;import java.security.*;import java.util.*;import java.util.zip.*;
public class BuildService extends Service {
 static volatile boolean running=false;private volatile boolean cancelled=false;private Thread thread;private CloudApi api;private JSONObject state;private String repo="";private long runId=0;
 public android.os.IBinder onBind(Intent i){return null;}
 void update(String text){getSharedPreferences("ui",0).edit().putString("status",text).apply();try(FileWriter f=new FileWriter(new File(getFilesDir(),"build.log"),true)){f.write(text+"\n");}catch(Exception ignored){}
  NotificationManager n=getSystemService(NotificationManager.class);n.notify(1,notice(text));}
 Notification notice(String text){return new Notification.Builder(this,"build").setSmallIcon(android.R.drawable.stat_sys_upload).setContentTitle("AndroidCompiler").setContentText(text).setOngoing(true).setContentIntent(PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT)).build();}
 public void onCreate(){super.onCreate();getSystemService(NotificationManager.class).createNotificationChannel(new NotificationChannel("build","בנייה בענן",NotificationManager.IMPORTANCE_LOW));}
 public int onStartCommand(Intent intent,int flags,int id){
  if(intent==null){stopSelf();return START_NOT_STICKY;}
  if("cancel".equals(intent.getAction())){cancelled=true;if(thread!=null)thread.interrupt();if(!running)stopSelf();return START_NOT_STICKY;}
  if(running)return START_NOT_STICKY;
  startForeground(1,notice("מתחבר לבנייה בענן"));running=true;cancelled=false;String token=intent.getStringExtra("token");boolean resume=intent.getBooleanExtra("resume",false);
  thread=new Thread(()->{api=new CloudApi(token==null?"":token);try{
   state=new JSONObject(new String(Files.readAllBytes(new File(getFilesDir(),"job.json").toPath()),java.nio.charset.StandardCharsets.UTF_8));
   if(resume){repo=state.getString("repository");runId=state.optLong("runId");}else upload();
   watch();download();update("הבנייה הסתיימה — הקבצים נשמרו בתיקיית היעד");
  }catch(Exception e){if(cancelled){cancelRemote();update("המעקב בוטל. בדוק את GitHub אם ביטול הבנייה מרחוק לא אושר.");}else update("הפעולה נכשלה: "+e.getMessage()+". אפשר לבדוק את הבנייה הקודמת או לפתוח GitHub.");}
  finally{new File(getCacheDir(),"output.zip").delete();api.clear();api=null;running=false;stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}},"cloud-build");thread.start();return START_NOT_STICKY;
 }
 void check()throws InterruptedException{if(cancelled)throw new InterruptedException("בוטל");}
 void save()throws Exception {File tmp=new File(getFilesDir(),"job.tmp");Files.write(tmp.toPath(),state.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));Files.move(tmp.toPath(),new File(getFilesDir(),"job.json").toPath(),StandardCopyOption.REPLACE_EXISTING);}
 JSONObject obj(Object... args)throws JSONException{JSONObject o=new JSONObject();for(int i=0;i<args.length;i+=2)o.put((String)args[i],args[i+1]);return o;}
 void upload()throws Exception {
  String name=state.getString("repoName");if(!name.matches("[A-Za-z0-9][A-Za-z0-9_.-]{0,70}"))throw new IOException("שם מאגר לא תקין");
  update("בודק חיבור GitHub ומאגר פרטי");repo=api.get("/user").getString("login")+"/"+name;JSONObject meta;
  try{meta=api.get("/repos/"+repo);}catch(FileNotFoundException e){meta=api.post("/user/repos",obj("name",name,"private",true,"auto_init",true));}
  if(!meta.getBoolean("private"))throw new IOException("יש לבחור מאגר פרטי בלבד");check();
  String head=api.get("/repos/"+repo+"/git/ref/heads/"+meta.getString("default_branch")).getJSONObject("object").getString("sha");
  String target=state.getString("target"),arch=state.getString("arch");
  Map<String,byte[]> payload=new LinkedHashMap<>();payload.put("source.zip",Files.readAllBytes(new File(getFilesDir(),"source.zip").toPath()));
  try(InputStream in=getAssets().open("cloud-engine.zip")){payload.put("engine.zip",CloudApi.bytes(in));}
  payload.put("build-config.json",state.getJSONObject("config").toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
  String template;try(InputStream in=getAssets().open("workflow.yml")){template=CloudApi.read(in);}
  String host=target.equals("apk")?"ubuntu-latest":target.equals("windows")?"windows-latest":arch.equals("arm64")?"macos-15":"macos-15-intel";
  payload.put(".github/workflows/build.yml",template.replace("RUNNER",host).getBytes(java.nio.charset.StandardCharsets.UTF_8));JSONArray tree=new JSONArray();
  for(Map.Entry<String,byte[]> f:payload.entrySet()){check();update("מעלה "+f.getKey());tree.put(obj("path",f.getKey(),"mode","100644","type","blob","sha",api.blob(repo,f.getValue())));}
  payload.clear();String treeId=api.post("/repos/"+repo+"/git/trees",obj("tree",tree)).getString("sha");
  String sha=api.post("/repos/"+repo+"/git/commits",obj("tree",treeId,"parents",new JSONArray().put(head),"message","Build source from AndroidCompiler")).getString("sha");
  String branch="ac-mobile-"+UUID.randomUUID();check();api.post("/repos/"+repo+"/git/refs",obj("ref","refs/heads/"+branch,"sha",head));
  api.api("/repos/"+repo+"/git/refs/heads/"+branch,obj("sha",sha,"force",false),"PATCH");
  state.put("repository",repo).put("sha",sha).put("branch",branch);save();getSharedPreferences("ui",0).edit().putString("url","https://github.com/"+repo+"/actions").apply();
  update("הקוד הועלה למאגר פרטי. הבנייה רצה בענן; הקוד נשאר בהיסטוריית המאגר.");
 }
 void watch()throws Exception {
  long start=System.currentTimeMillis();String previous="";
  while(System.currentTimeMillis()-start<60*60*1000){check();JSONArray runs=api.get("/repos/"+repo+"/actions/runs?head_sha="+state.getString("sha")).getJSONArray("workflow_runs");
   if(runs.length()>0){JSONObject run=runs.getJSONObject(0);runId=run.getLong("id");state.put("runId",runId);save();getSharedPreferences("ui",0).edit().putString("url",run.getString("html_url")).apply();
    if(run.getString("status").equals("completed")){if(!run.optString("conclusion").equals("success"))throw new IOException("הבנייה הסתיימה במצב "+run.optString("conclusion")+". פתח את לוג GitHub");return;}
    String status=run.getString("status");JSONArray jobs=api.get("/repos/"+repo+"/actions/runs/"+runId+"/jobs").getJSONArray("jobs");
    for(int j=0;j<jobs.length();j++){JSONArray steps=jobs.getJSONObject(j).optJSONArray("steps");if(steps==null)continue;for(int k=0;k<steps.length();k++)if(steps.getJSONObject(k).optString("status").equals("in_progress"))status=steps.getJSONObject(k).getString("name");}
    if(!status.equals(previous)){update("בענן: "+status);previous=status;}
   }else if(previous.isEmpty()){update("ממתין לתחילת GitHub Actions");previous="waiting";}
   Thread.sleep(15000);
  }throw new IOException("ההמתנה הסתיימה. אפשר לחזור ולבדוק את הבנייה הקודמת.");
 }
 void cancelRemote(){if(api==null||repo.isEmpty())return;try{
  if(runId==0&&state.has("sha")){JSONArray runs=api.get("/repos/"+repo+"/actions/runs?head_sha="+state.getString("sha")).getJSONArray("workflow_runs");if(runs.length()>0)runId=runs.getJSONObject(0).getLong("id");}
  if(runId>0)api.post("/repos/"+repo+"/actions/runs/"+runId+"/cancel",new JSONObject());
 }catch(Exception e){update("לא ניתן לאשר ביטול מרחוק — פתח GitHub Actions");}}
 void download()throws Exception{
  update("מוריד את תוצרי הבנייה");JSONArray list=api.get("/repos/"+repo+"/actions/runs/"+runId+"/artifacts").getJSONArray("artifacts");JSONObject a=null;
  for(int i=0;i<list.length();i++)if(list.getJSONObject(i).getString("name").equals("build-output")&&!list.getJSONObject(i).getBoolean("expired"))a=list.getJSONObject(i);
  if(a==null)throw new IOException("לא נמצא תוצר להורדה");String url=api.artifactUrl(repo,a.getLong("id"));File zip=new File(getCacheDir(),"output.zip");HttpURLConnection c=(HttpURLConnection)new URL(url).openConnection();c.setConnectTimeout(30000);c.setReadTimeout(60000);
  MessageDigest hash=MessageDigest.getInstance("SHA-256");long size=0;try(InputStream in=c.getInputStream();OutputStream out=new FileOutputStream(zip)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){check();if((size+=n)>1024L*1024*1024)throw new IOException("התוצר גדול מ־1 GiB");hash.update(b,0,n);out.write(b,0,n);}}finally{c.disconnect();}
  StringBuilder hex=new StringBuilder();for(byte b:hash.digest())hex.append(String.format("%02x",b&255));String digest=a.optString("digest","");if(!digest.isEmpty()&&!digest.equals("null")&&!digest.equals("sha256:"+hex))throw new IOException("בדיקת תקינות ההורדה נכשלה");
  Uri tree=Uri.parse(state.getString("destination"));Uri parent=DocumentsContract.buildDocumentUriUsingTree(tree,DocumentsContract.getTreeDocumentId(tree));Uri folder=DocumentsContract.createDocument(getContentResolver(),parent,DocumentsContract.Document.MIME_TYPE_DIR,"Build-"+System.currentTimeMillis());if(folder==null)throw new IOException("לא ניתן ליצור תיקיית תוצרים");
  Map<String,Uri> folders=new HashMap<>();folders.put("",folder);long total=0;int count=0;
  try(ZipFile z=new ZipFile(zip)){
   Enumeration<? extends ZipEntry> all=z.entries();while(all.hasMoreElements()){ZipEntry e=all.nextElement();SourceZip.safe(e.getName());if(++count>30000||e.getSize()<0||(total+=e.getSize())>1024L*1024*1024)throw new IOException("תוצר גדול מדי");}
   all=z.entries();while(all.hasMoreElements()){check();ZipEntry e=all.nextElement();if(e.isDirectory())continue;String[] parts=e.getName().split("/");String path="";Uri dir=folder;
    for(int i=0;i<parts.length-1;i++){path+=parts[i]+"/";if(!folders.containsKey(path))folders.put(path,DocumentsContract.createDocument(getContentResolver(),dir,DocumentsContract.Document.MIME_TYPE_DIR,parts[i]));dir=folders.get(path);if(dir==null)throw new IOException("לא ניתן ליצור תיקייה");}
    String name=parts[parts.length-1];String mime=name.endsWith(".apk")?"application/vnd.android.package-archive":"application/octet-stream";Uri file=DocumentsContract.createDocument(getContentResolver(),dir,mime,name);if(file==null)throw new IOException("לא ניתן לשמור קובץ");
    try(InputStream in=z.getInputStream(e);OutputStream out=getContentResolver().openOutputStream(file)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){check();out.write(b,0,n);}}
   }
   getSharedPreferences("ui",0).edit().putString("output",folder.toString()).apply();
  }catch(Exception e){try{DocumentsContract.deleteDocument(getContentResolver(),folder);}catch(Exception ignored){}throw e;}finally{zip.delete();}
 }
 @Override public void onTimeout(int id,int type){cancelled=true;if(thread!=null)thread.interrupt();stopSelf();}
}

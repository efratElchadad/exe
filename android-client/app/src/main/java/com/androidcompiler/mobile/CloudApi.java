package com.androidcompiler.mobile;
import org.json.*;
import android.util.Base64;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
final class CloudApi {
 private String token;
 CloudApi(String t){token=t;}
 void clear(){token="";}
 JSONObject api(String path,JSONObject data,String method)throws Exception {
  HttpURLConnection c=(HttpURLConnection)new URL("https://api.github.com"+path).openConnection();
  c.setInstanceFollowRedirects(false);c.setConnectTimeout(30000);c.setReadTimeout(60000);c.setRequestMethod(method);
  c.setRequestProperty("Authorization","Bearer "+token);c.setRequestProperty("Accept","application/vnd.github+json");c.setRequestProperty("User-Agent","AndroidCompiler-Mobile");
  try{
   if(data!=null){c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");try(OutputStream o=c.getOutputStream()){o.write(data.toString().getBytes(StandardCharsets.UTF_8));}}
   int status=c.getResponseCode();if(status==404)throw new FileNotFoundException("GitHub resource not found");
   if(status<200||status>=300)throw new IOException("GitHub HTTP "+status+" — בדוק הרשאות אסימון, מכסה וחיבור");
   String body=read(c.getInputStream());return body.isEmpty()?new JSONObject():new JSONObject(body);
  }finally{c.disconnect();}
 }
 JSONObject get(String p)throws Exception{return api(p,null,"GET");}
 JSONObject post(String p,JSONObject d)throws Exception{return api(p,d,"POST");}
 String blob(String repo,byte[] b)throws Exception{return post("/repos/"+repo+"/git/blobs",new JSONObject().put("content",Base64.encodeToString(b,Base64.NO_WRAP)).put("encoding","base64")).getString("sha");}
 String artifactUrl(String repo,long id)throws Exception {
  HttpURLConnection c=(HttpURLConnection)new URL("https://api.github.com/repos/"+repo+"/actions/artifacts/"+id+"/zip").openConnection();
  c.setInstanceFollowRedirects(false);c.setConnectTimeout(30000);c.setReadTimeout(30000);c.setRequestProperty("Authorization","Bearer "+token);c.setRequestProperty("User-Agent","AndroidCompiler-Mobile");
  try{if(c.getResponseCode()!=302)throw new IOException("הורדת התוצר נכשלה");String url=c.getHeaderField("Location");if(url==null||!url.startsWith("https://"))throw new IOException("כתובת הורדה לא מאובטחת");return url;}finally{c.disconnect();}
 }
 static byte[] bytes(InputStream in)throws IOException{ByteArrayOutputStream b=new ByteArrayOutputStream();byte[] buf=new byte[8192];int n;while((n=in.read(buf))!=-1)b.write(buf,0,n);return b.toByteArray();}
 static String read(InputStream in)throws IOException {try(InputStream x=in;ByteArrayOutputStream b=new ByteArrayOutputStream()){byte[] buf=new byte[8192];int n;while((n=x.read(buf))!=-1){b.write(buf,0,n);if(b.size()>16*1024*1024)throw new IOException("תגובה גדולה מדי");}return b.toString("UTF-8");}}
}

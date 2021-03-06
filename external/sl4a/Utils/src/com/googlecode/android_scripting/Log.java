/*
 * Copyright (C) 2017 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.googlecode.android_scripting;

import android.app.AlertDialog;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.DialogInterface;
import android.widget.Toast;

public class Log {
  private static final String CHANNEL_ID = "log_channel";
  private Log() {
    // Utility class.
  }

  private static String getTag() {
    StackTraceElement[] stackTraceElements = Thread.currentThread().getStackTrace();
    String fullClassName = stackTraceElements[4].getClassName();
    String className = fullClassName.substring(fullClassName.lastIndexOf(".") + 1);
    int lineNumber = stackTraceElements[4].getLineNumber();
    return "sl4a." + className + ":" + lineNumber;
  }

  private static void toast(Context context, String message) {
    Toast.makeText(context, message, Toast.LENGTH_SHORT).show();
  }

  private static int getStringId(String identifier, Context context) {
    String packageName = context.getPackageName();
    return context.getResources().getIdentifier(identifier, "string", packageName);
  }

  private static void createNotificationChannel(Context context, NotificationManager notificationManager) {
    CharSequence name = context.getString(getStringId("notification_channel_name", context));
    String description = context.getString(getStringId("notification_channel_description", context));
    int importance = NotificationManager.IMPORTANCE_DEFAULT;
    NotificationChannel channel = new NotificationChannel(CHANNEL_ID, name, importance);
    channel.setDescription(description);
    channel.enableLights(false);
    channel.enableVibration(false);
    notificationManager.createNotificationChannel(channel);
  }

  public static void notify(Context context, String title, String contentTitle, String message) {
    android.util.Log.v(getTag(), String.format("%s %s", contentTitle, message));

    NotificationManager notificationManager =
        (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
    createNotificationChannel(context, notificationManager);

    String packageName = context.getPackageName();
    int iconId = context.getResources().getIdentifier("stat_sys_warning", "drawable", packageName);
    Notification.Builder builder = new Notification.Builder(context, CHANNEL_ID);
    builder.setSmallIcon(iconId > 0 ? iconId : -1)
           .setTicker(title)
           .setWhen(0)
           .setContentTitle(contentTitle)
           .setContentText(message)
           .setContentIntent(PendingIntent.getService(context, 0, null,
                   PendingIntent.FLAG_IMMUTABLE));
    Notification note = builder.build();
    note.contentView.getLayoutId();
    notificationManager.notify(NotificationIdFactory.create(), note);
  }

  public static void showDialog(final Context context, final String title, final String message) {
    android.util.Log.v(getTag(), String.format("%s %s", title, message));

    MainThread.run(context, new Runnable() {
      @Override
      public void run() {
        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle(title);
        builder.setMessage(message);

        DialogInterface.OnClickListener buttonListener = new DialogInterface.OnClickListener() {
          @Override
          public void onClick(DialogInterface dialog, int which) {
            dialog.dismiss();
          }
        };
        builder.setPositiveButton("Ok", buttonListener);
        builder.show();
      }
    });
  }

  public static void v(String message) {
    android.util.Log.v(getTag(), message);
  }

  public static void v(String message, Throwable e) {
    android.util.Log.v(getTag(), message, e);
  }

  public static void v(Context context, String message) {
    toast(context, message);
    android.util.Log.v(getTag(), message);
  }

  public static void v(Context context, String message, Throwable e) {
    toast(context, message);
    android.util.Log.v(getTag(), message, e);
  }

  public static void e(Throwable e) {
    android.util.Log.e(getTag(), "Error", e);
  }

  public static void e(String message) {
    android.util.Log.e(getTag(), message);
  }

  public static void e(String message, Throwable e) {
    android.util.Log.e(getTag(), message, e);
  }

  public static void e(Context context, String message) {
    toast(context, message);
    android.util.Log.e(getTag(), message);
  }

  public static void e(Context context, String message, Throwable e) {
    toast(context, message);
    android.util.Log.e(getTag(), message, e);
  }

  public static void w(Throwable e) {
    android.util.Log.w(getTag(), "Warning", e);
  }

  public static void w(String message) {
    android.util.Log.w(getTag(), message);
  }

  public static void w(String message, Throwable e) {
    android.util.Log.w(getTag(), message, e);
  }

  public static void w(Context context, String message) {
    toast(context, message);
    android.util.Log.w(getTag(), message);
  }

  public static void w(Context context, String message, Throwable e) {
    toast(context, message);
    android.util.Log.w(getTag(), message, e);
  }

  public static void d(String message) {
    android.util.Log.d(getTag(), message);
  }

  public static void d(String message, Throwable e) {
    android.util.Log.d(getTag(), message, e);
  }

  public static void d(Context context, String message) {
    toast(context, message);
    android.util.Log.d(getTag(), message);
  }

  public static void d(Context context, String message, Throwable e) {
    toast(context, message);
    android.util.Log.d(getTag(), message, e);
  }

  public static void i(String message) {
    android.util.Log.i(getTag(), message);
  }

  public static void i(String message, Throwable e) {
    android.util.Log.i(getTag(), message, e);
  }

  public static void i(Context context, String message) {
    toast(context, message);
    android.util.Log.i(getTag(), message);
  }

  public static void i(Context context, String message, Throwable e) {
    toast(context, message);
    android.util.Log.i(getTag(), message, e);
  }
}

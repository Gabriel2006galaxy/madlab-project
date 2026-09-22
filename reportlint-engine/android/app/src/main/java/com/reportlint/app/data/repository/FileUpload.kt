package com.reportlint.app.data.repository

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

private const val DOCX_MEDIA_TYPE =
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

fun uriToMultipart(context: Context, uri: Uri, formFieldName: String): MultipartBody.Part {
    val filename = queryDisplayName(context, uri) ?: "upload.docx"
    val cacheFile = File(context.cacheDir, "upload_${System.currentTimeMillis()}_$filename")

    context.contentResolver.openInputStream(uri)?.use { input ->
        cacheFile.outputStream().use { output -> input.copyTo(output) }
    } ?: error("Could not open the selected file")

    val requestBody = cacheFile.asRequestBody(DOCX_MEDIA_TYPE.toMediaTypeOrNull())
    return MultipartBody.Part.createFormData(formFieldName, filename, requestBody)
}

private fun queryDisplayName(context: Context, uri: Uri): String? {
    context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
        val nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
        if (nameIndex >= 0 && cursor.moveToFirst()) {
            return cursor.getString(nameIndex)
        }
    }
    return null
}

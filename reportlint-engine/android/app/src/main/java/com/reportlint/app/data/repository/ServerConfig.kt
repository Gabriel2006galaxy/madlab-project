package com.reportlint.app.data.repository

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "reportlint_settings")

private val SERVER_URL_KEY = stringPreferencesKey("server_url")
const val DEFAULT_SERVER_URL = "http://10.0.2.2:8000/"

class ServerConfig(private val context: Context) {

    val serverUrl: Flow<String> = context.dataStore.data.map { prefs ->
        prefs[SERVER_URL_KEY] ?: DEFAULT_SERVER_URL
    }

    suspend fun setServerUrl(url: String) {
        context.dataStore.edit { prefs -> prefs[SERVER_URL_KEY] = url }
    }
}

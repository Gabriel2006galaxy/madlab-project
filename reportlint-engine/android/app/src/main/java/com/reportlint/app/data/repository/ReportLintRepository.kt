package com.reportlint.app.data.repository

import android.content.Context
import android.net.Uri
import com.reportlint.app.data.model.ComplianceResult
import com.reportlint.app.data.model.RuleSet
import com.reportlint.app.data.model.Template
import com.reportlint.app.data.model.TemplateSummary
import com.reportlint.app.data.network.ApiClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext

class ReportLintRepository(
    private val context: Context,
    private val serverConfig: ServerConfig
) {
    private suspend fun api() = ApiClient.create(serverConfig.serverUrl.first())

    suspend fun uploadTemplate(uri: Uri): Result<Template> = withContext(Dispatchers.IO) {
        runCatching {
            val part = uriToMultipart(context, uri, "file")
            api().uploadTemplate(part)
        }
    }

    suspend fun listTemplates(): Result<List<TemplateSummary>> = withContext(Dispatchers.IO) {
        runCatching { api().listTemplates() }
    }

    suspend fun getTemplate(id: String): Result<Template> = withContext(Dispatchers.IO) {
        runCatching { api().getTemplate(id) }
    }

    suspend fun updateRules(id: String, ruleset: RuleSet): Result<Template> = withContext(Dispatchers.IO) {
        runCatching { api().updateRules(id, ruleset) }
    }

    suspend fun publishTemplate(id: String): Result<Template> = withContext(Dispatchers.IO) {
        runCatching { api().publishTemplate(id) }
    }

    suspend fun deleteTemplate(id: String): Result<Unit> = withContext(Dispatchers.IO) {
        runCatching { api().deleteTemplate(id); Unit }
    }

    suspend fun checkReport(templateId: String, uri: Uri): Result<ComplianceResult> =
        withContext(Dispatchers.IO) {
            runCatching {
                val part = uriToMultipart(context, uri, "report")
                api().checkReport(templateId, part)
            }
        }
}

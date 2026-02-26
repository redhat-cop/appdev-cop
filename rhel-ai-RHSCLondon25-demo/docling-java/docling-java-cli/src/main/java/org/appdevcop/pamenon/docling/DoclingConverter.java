package org.appdevcop.pamenon.docling;

import ai.docling.serve.api.DoclingServeApi;
import ai.docling.serve.api.convert.request.ConvertDocumentRequest;
import ai.docling.serve.api.convert.request.options.ConvertDocumentOptions;
import ai.docling.serve.api.convert.request.options.OutputFormat;

import ai.docling.serve.api.convert.request.source.FileSource;
import ai.docling.serve.api.convert.request.target.InBodyTarget;
import ai.docling.serve.api.convert.response.ConvertDocumentResponse;

import java.io.File;
import java.net.URI;
import java.nio.file.Files;
import java.util.Base64;
import java.util.List;

public class DoclingConverter {

    private final DoclingServeApi api;

    public DoclingConverter(String baseUrl) {
        this.api = DoclingServeApi.builder()
                .baseUrl(baseUrl)
                .logRequests()
                .logResponses()
                .prettyPrint()
                .build();
    }

    public ConvertDocumentResponse convert(File file, OutputFormat format) throws Exception {

        byte[] bytes = Files.readAllBytes(file.toPath());

        String base64 = Base64.getEncoder().encodeToString(bytes);
        // Wrap in a list because server expects array
        List<FileSource> files = List.of(
                FileSource.builder()
                        .filename(file.getName())
                        .base64String(Base64.getEncoder().encodeToString(Files.readAllBytes(file.toPath())))
                        .build()
        );

        ConvertDocumentRequest request = ConvertDocumentRequest.builder()
                .sources(files)
                .options(ConvertDocumentOptions.builder()
                        .toFormat(format)
                        .includeImages(true)
                        .build())
                .target(InBodyTarget.builder().build())
                .build();

        ConvertDocumentResponse response = api.convertFiles(request,file.toPath());

        System.out.println(response.getDocument().getMarkdownContent());




        return response;
    }
}
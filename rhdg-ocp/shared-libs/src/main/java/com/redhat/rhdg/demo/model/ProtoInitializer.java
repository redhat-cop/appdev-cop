package com.redhat.rhdg.demo.model;

import org.infinispan.protostream.GeneratedSchema;
import org.infinispan.protostream.annotations.AutoProtoSchemaBuilder;

@AutoProtoSchemaBuilder(
		basePackages = "com.redhat.rhdg.demo.model.proto",
		schemaFileName = "model.proto",
		schemaFilePath = "proto/",
		schemaPackageName = "rhdg_demo")
public interface ProtoInitializer extends GeneratedSchema {

}

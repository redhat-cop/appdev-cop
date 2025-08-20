package com.redhat.rhdg.demo.model.proto;

import org.infinispan.api.annotations.indexing.Basic;
import org.infinispan.api.annotations.indexing.Indexed;
import org.infinispan.protostream.annotations.ProtoFactory;
import org.infinispan.protostream.annotations.ProtoField;

@Indexed
public class ProtoValue {

	@ProtoField(1)
	@Basic
	String data;
	
	@ProtoFactory
	public ProtoValue(String data) {
		this.data = data;
	}

	public String getData() {
		return data;
	}

	public void setData(String data) {
		this.data = data;
	}

	@Override
	public String toString() {
		return "ProtoValue [data=" + data + "]";
	}
}

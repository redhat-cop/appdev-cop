package com.redhat.rhdg.demo.model.proto;

import org.infinispan.protostream.annotations.ProtoFactory;
import org.infinispan.protostream.annotations.ProtoField;

public class ProtoKey {

	@ProtoField(1)
	String uid;
	
	@ProtoFactory
	public ProtoKey(String uid) {
		this.uid = uid;
	}

	public String getUid() {
		return uid;
	}

	public void setUid(String uid) {
		this.uid = uid;
	}

	@Override
	public String toString() {
		return "ProtoKey [uid=" + uid + "]";
	}
}

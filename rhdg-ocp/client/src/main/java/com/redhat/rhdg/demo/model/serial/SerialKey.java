package com.redhat.rhdg.demo.model.serial;

import java.io.Serializable;

public class SerialKey implements Serializable {

	private static final long serialVersionUID = 8438408087786321084L;
	
	String uid;
	
	public SerialKey(String uid) {
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
		return "SerialKey [uid=" + uid + "]";
	}
}

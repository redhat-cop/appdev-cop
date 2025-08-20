package com.redhat.rhdg.demo.model.serial;

import java.io.Serializable;

public class SerialValue implements Serializable {

	private static final long serialVersionUID = -4026880096294884079L;

	String data;
	
	public SerialValue(String data) {
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
		return "SerialValue [data=" + data + "]";
	}
}

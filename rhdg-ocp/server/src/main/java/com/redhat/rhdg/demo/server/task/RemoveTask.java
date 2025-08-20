package com.redhat.rhdg.demo.server.task;

import org.infinispan.tasks.ServerTask;
import org.infinispan.tasks.TaskContext;
import org.infinispan.tasks.TaskExecutionMode;

import com.redhat.rhdg.demo.model.proto.ProtoKey;

public class RemoveTask implements ServerTask<String> {

	private TaskContext context;

	public String call() throws Exception {
		final String parameter = (String) context.getParameters().get().getOrDefault("uid", null);
		if (parameter != null) {
			context.getCache().ifPresent(cache -> cache.remove(new ProtoKey(parameter)));
		}
		return parameter;
	}

	public String getName() {
		return "removeTask";
	}

	public void setTaskContext(TaskContext taskContext) {
		this.context = taskContext;
	}

	public TaskExecutionMode getExecutionMode() {
		return TaskExecutionMode.ALL_NODES;
	}

}
